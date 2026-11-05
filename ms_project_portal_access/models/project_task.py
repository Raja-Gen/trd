# -*- coding: utf-8 -*-
from markupsafe import Markup

from odoo import Command, _, api, fields, models
from odoo.exceptions import ValidationError


class ProjectTask(models.Model):
    _inherit = "project.task"

    ms_portal_partner_ids = fields.Many2many(
        "res.partner",
        "ms_project_task_portal_partner_rel",
        "task_id",
        "partner_id",
        string="Portal Users",
        copy=False,
        help="These portal users can open this task and its subtasks on the portal, "
             "edit them and change their status. They do not see the other tasks of "
             "the project. A contact needs portal access first (Contacts > Action > "
             "Grant portal access).",
    )
    ms_portal_enabled = fields.Boolean(
        related="company_id.ms_project_portal",
        string="Portal Access Per Task",
    )

    # ------------------------------------------------------------------
    # Keeping the grants and Odoo's own access records in step
    # ------------------------------------------------------------------
    def _ms_portal_grant(self, partners, notify=True):
        """Give what project sharing needs: a limited collaborator who follows
        the project and the task. Core's own rules and board do the rest."""
        self.ensure_one()
        project = self.project_id
        if not project or not self.ms_portal_enabled:
            raise ValidationError(_(
                "Portal Users can only be set on a task in a project of a company "
                "that has portal access per task enabled."))
        not_portal = partners.filtered(lambda p: not any(user._is_portal() for user in p.user_ids))
        if not_portal:
            raise ValidationError(_(
                "%(names)s cannot be given access because they are not portal users. "
                "Grant them portal access from the contact first.",
                names=", ".join(not_portal.mapped("display_name"))))

        if project.privacy_visibility == "employees":
            project.privacy_visibility = "portal"
        project._add_collaborators(partners, limited_access=True)
        project.message_subscribe(partner_ids=partners.ids)
        self.message_subscribe(partner_ids=partners.ids)
        # The company rule hides the task from a user who is not in its company.
        users = partners.user_ids.filtered(lambda user: self.company_id not in user.company_ids)
        users.write({"company_ids": [Command.link(self.company_id.id)]})
        if notify and not self.env.context.get("ms_portal_no_notify"):
            self._ms_portal_notify(partners)

    def _ms_portal_notify(self, partners):
        self.ensure_one()
        url = "%s/my/projects/%s/project_sharing" % (self.get_base_url(), self.project_id.id)
        self.message_notify(
            subject=_("You have been given access to %s", self.display_name),
            body=Markup("<p>%s</p><p><a href='%s'>%s</a></p>") % (
                _("You have been given access to the task %(task)s of the project %(project)s.",
                  task=self.display_name, project=self.project_id.display_name),
                url,
                _("Open the project"),
            ),
            partner_ids=partners.ids,
            email_layout_xmlid="mail.mail_notification_light",
        )

    def _ms_portal_release(self, project, partners):
        """A limited collaborator with no task left has no reason to stay on the project."""
        for partner in partners:
            collaborator = project.collaborator_ids.filtered(lambda c: c.partner_id == partner)
            if not collaborator.limited_access:
                continue
            still_granted = self.with_context(active_test=False).search_count([
                ("project_id", "=", project.id),
                ("ms_portal_partner_ids", "in", partner.ids),
            ], limit=1)
            if not still_granted:
                project.message_unsubscribe(partner_ids=partner.ids)

    def _ms_portal_subtasks(self):
        return self.with_context(active_test=False)._get_all_subtasks() - self

    def _ms_portal_sync(self, before):
        """Apply what changed; ``before`` maps a task id to (project, partners)."""
        for task in self:
            old_project, old_partners = before[task.id]
            added = task.ms_portal_partner_ids - old_partners
            removed = old_partners - task.ms_portal_partner_ids
            moved = task.project_id != old_project

            if moved and old_project:
                remaining = old_partners & task.ms_portal_partner_ids
                task._ms_portal_release(old_project, remaining)
            if removed:
                task.with_context(ms_portal_skip_sync=True).message_unsubscribe(partner_ids=removed.ids)
            to_grant = task.ms_portal_partner_ids if moved else added
            if to_grant:
                task._ms_portal_grant(to_grant, notify=bool(added))
            if added or removed:
                subtasks = task._ms_portal_subtasks().filtered(lambda t: t.project_id and t.ms_portal_enabled)
                if subtasks:
                    subtasks.with_context(ms_portal_no_notify=True).write({"ms_portal_partner_ids": [
                        *[Command.link(partner.id) for partner in added],
                        *[Command.unlink(partner.id) for partner in removed],
                    ]})
            if removed:
                task._ms_portal_release(task.project_id, removed)

    @api.model_create_multi
    def create(self, vals_list):
        tasks = super().create(vals_list)
        if self.env.context.get("ms_portal_skip_sync"):
            return tasks
        for task in tasks.sudo():
            # Core subscribes a subtask to its parent's followers, so its grants come too.
            inherited = task.parent_id.ms_portal_partner_ids if task.ms_portal_enabled else self.env["res.partner"]
            partners = task.ms_portal_partner_ids
            if inherited - partners:
                task.with_context(ms_portal_skip_sync=True).ms_portal_partner_ids |= inherited
            if partners or inherited:
                task._ms_portal_grant(partners | inherited, notify=bool(partners))
        return tasks

    def write(self, vals):
        if self.env.context.get("ms_portal_skip_sync") or not {"ms_portal_partner_ids", "project_id"} & vals.keys():
            return super().write(vals)
        tasks = self.sudo()
        before = {task.id: (task.project_id, task.ms_portal_partner_ids) for task in tasks}
        res = super().write(vals)
        tasks._ms_portal_sync(before)
        return res

    def unlink(self):
        granted = [(task.project_id, task.ms_portal_partner_ids)
                   for task in self.sudo() if task.ms_portal_partner_ids and task.project_id]
        res = super().unlink()
        for project, partners in granted:
            self.env["project.task"].sudo()._ms_portal_release(project, partners)
        return res

    def message_unsubscribe(self, partner_ids=None):
        # Removing a follower in the chatter takes the access away, so the field follows.
        res = super().message_unsubscribe(partner_ids=partner_ids)
        if partner_ids and not self.env.context.get("ms_portal_skip_sync"):
            partners = self.env["res.partner"].browse(partner_ids)
            for task in self.sudo():
                if task.ms_portal_partner_ids & partners:
                    task.ms_portal_partner_ids -= partners
        return res

    def _message_auto_subscribe(self, updated_values, followers_existing_policy="skip"):
        # Core adds every portal follower of the project to a task created in it,
        # and following is what gives a limited collaborator access to a task.
        tasks = self.sudo().filtered(
            lambda t: t.project_id.company_id.ms_project_portal and t.project_id.collaborator_ids.filtered("limited_access"))
        before = {task.id: task.message_partner_ids for task in tasks}
        res = super()._message_auto_subscribe(updated_values, followers_existing_policy=followers_existing_policy)
        for task in tasks:
            limited = task.project_id.collaborator_ids.filtered("limited_access").partner_id
            strays = (task.message_partner_ids - before[task.id]) & limited
            strays -= task.ms_portal_partner_ids | task.partner_id
            if strays:
                task.with_context(ms_portal_skip_sync=True).message_unsubscribe(partner_ids=strays.ids)
        return res

    # ------------------------------------------------------------------
    # Chatter
    # ------------------------------------------------------------------
    @api.model
    def _get_thread_with_access(self, thread_id, *, project_sharing_id=None, token=None, **kwargs):
        # Core only checks that the portal user is on the project, and then hands
        # over the task's token: a limited collaborator could read and post on any
        # task of it by changing the id.
        if project_sharing_id and self.env.user._is_portal():
            task = self.browse(thread_id).exists()
            if task.sudo().ms_portal_enabled and not task.has_access("read"):
                return self.browse()
        return super()._get_thread_with_access(
            thread_id, project_sharing_id=project_sharing_id, token=token, **kwargs)
