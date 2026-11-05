# -*- coding: utf-8 -*-
from odoo import models


class ProjectProject(models.Model):
    _inherit = "project.project"

    def _ms_portal_forget(self, partners):
        """Drop the grants of these partners on the tasks of these projects."""
        tasks = self.env["project.task"].sudo().with_context(active_test=False).search([
            ("project_id", "in", self.ids),
            ("ms_portal_partner_ids", "in", partners.ids),
        ])
        for task in tasks:
            task.with_context(ms_portal_skip_sync=True).ms_portal_partner_ids -= partners

    def message_unsubscribe(self, partner_ids=None):
        # Core drops the collaborators and the task followers here, which is also
        # what happens when a project stops being shared. The context stops the
        # task override from coming back to this project for every task.
        res = super(ProjectProject, self.with_context(ms_portal_skip_sync=True)).message_unsubscribe(
            partner_ids=partner_ids)
        if partner_ids:
            self.sudo()._ms_portal_forget(self.env["res.partner"].browse(partner_ids))
        return res
