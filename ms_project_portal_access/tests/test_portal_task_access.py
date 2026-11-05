# -*- coding: utf-8 -*-
import json

from lxml import etree

from odoo.exceptions import AccessError, ValidationError
from odoo.tests.common import HttpCase, TransactionCase, new_test_user, tagged


class MsPortalCommon:

    @classmethod
    def _setup_data(cls):
        Company = cls.env["res.company"]
        cls.ms = Company.create({"name": "MS Portal Co", "ms_project_portal": True})
        cls.other = Company.create({"name": "MS Portal Other Co"})
        cls.env.user.company_ids |= cls.ms | cls.other

        def portal(login, company, parent=False):
            user = new_test_user(
                cls.env, login=login, groups="base.group_portal",
                company_id=company.id, company_ids=[(6, 0, company.ids)])
            user.partner_id.parent_id = parent
            return user

        cls.customer = cls.env["res.partner"].create({"name": "MS Customer Co", "is_company": True})
        cls.user_x = portal("ms_portal_x", cls.ms, cls.customer.id)
        cls.user_y = portal("ms_portal_y", cls.ms, cls.customer.id)
        cls.user_colleague = portal("ms_portal_colleague", cls.ms, cls.customer.id)
        cls.user_elsewhere = portal("ms_portal_elsewhere", cls.other)
        cls.user_project = new_test_user(
            cls.env, login="ms_portal_projectuser", groups="project.group_project_user",
            company_id=cls.ms.id, company_ids=[(6, 0, cls.ms.ids)])

        cls.stage_new = cls.env["project.task.type"].create({"name": "MS New Stage", "sequence": 1})
        cls.stage_done = cls.env["project.task.type"].create({"name": "MS Done Stage", "sequence": 2})
        stages = [(6, 0, (cls.stage_new | cls.stage_done).ids)]
        cls.project = cls.env["project.project"].create({
            "name": "MS Portal Project", "company_id": cls.ms.id,
            "privacy_visibility": "portal", "type_ids": stages,
        })
        cls.project_2 = cls.env["project.project"].create({
            "name": "MS Portal Project 2", "company_id": cls.ms.id,
            "privacy_visibility": "portal", "type_ids": stages,
        })
        cls.project_other = cls.env["project.project"].create({
            "name": "MS Other Project", "company_id": cls.other.id,
            "privacy_visibility": "portal", "type_ids": stages,
        })
        cls.task_a = cls._task("MS Granted Task")
        cls.task_b = cls._task("MS Hidden Task")

    @classmethod
    def _task(cls, name, project=None, **vals):
        project = project or cls.project
        return cls.env["project.task"].with_company(project.company_id).create({
            "name": name, "project_id": project.id, "stage_id": cls.stage_new.id, **vals})

    def _grant(self, task, *users):
        task.ms_portal_partner_ids |= self.env["res.partner"].union(*[u.partner_id for u in users])

    def _visible(self, user, *tasks):
        found = self.env["project.task"].with_user(user).search([("id", "in", [t.id for t in tasks])])
        return found


@tagged("post_install", "-at_install")
class TestPortalTaskAccess(MsPortalCommon, TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_data()

    # --- giving access --------------------------------------------------------

    def test_grant_sets_up_project_sharing(self):
        self._grant(self.task_a, self.user_x)
        collaborator = self.project.collaborator_ids.filtered(lambda c: c.partner_id == self.user_x.partner_id)
        self.assertTrue(collaborator.limited_access, "one task must not open the whole project")
        self.assertIn(self.user_x.partner_id, self.project.message_partner_ids)
        self.assertIn(self.user_x.partner_id, self.task_a.message_partner_ids)
        self.assertTrue(self.project.with_user(self.user_x)._check_project_sharing_access())

    def test_project_user_who_is_not_a_manager_can_grant(self):
        self.task_a.with_user(self.user_project).ms_portal_partner_ids |= self.user_x.partner_id
        self.assertEqual(self._visible(self.user_x, self.task_a), self.task_a)

    def test_grant_makes_a_employees_only_project_shared(self):
        self.project.privacy_visibility = "employees"
        self._grant(self.task_a, self.user_x)
        self.assertEqual(self.project.privacy_visibility, "portal")
        self.assertEqual(self._visible(self.user_x, self.task_a), self.task_a)

    def test_portal_user_of_another_company_gets_the_company(self):
        self._grant(self.task_a, self.user_elsewhere)
        self.assertIn(self.ms, self.user_elsewhere.company_ids)
        self.assertEqual(self._visible(self.user_elsewhere, self.task_a), self.task_a)

    def test_only_portal_users_can_be_given_access(self):
        for partner in (self.user_project.partner_id,
                        self.env["res.partner"].create({"name": "MS No User"})):
            with self.assertRaises(ValidationError):
                self.task_a.ms_portal_partner_ids |= partner

    def test_the_user_is_told(self):
        self._grant(self.task_a, self.user_x)
        messages = self.env["mail.message"].search([
            ("model", "=", "project.task"), ("res_id", "=", self.task_a.id),
            ("subject", "ilike", "given access"),
        ])
        self.assertIn(self.user_x.partner_id, messages.partner_ids)

    # --- what the portal user can do ------------------------------------------

    def test_sees_only_the_task_given(self):
        self._grant(self.task_a, self.user_x)
        self._grant(self.task_b, self.user_y)
        self.assertEqual(self._visible(self.user_x, self.task_a, self.task_b), self.task_a)
        self.assertEqual(self._visible(self.user_y, self.task_a, self.task_b), self.task_b)
        with self.assertRaises(AccessError):
            self.task_b.with_user(self.user_x).read(["name"])

    def test_can_edit_and_change_status(self):
        self._grant(self.task_a, self.user_x)
        tag = self.env["project.tags"].create({"name": "MS Portal Tag"})
        task = self.task_a.with_user(self.user_x)
        task.write({
            "name": "MS Edited",
            "description": "<p>MS typed</p>",
            "stage_id": self.stage_done.id,
            "state": "1_done",
            "priority": "1",
            "date_deadline": "2030-01-01 00:00:00",
            "tag_ids": [(4, tag.id)],
        })
        self.assertEqual(self.task_a.name, "MS Edited")
        self.assertEqual(self.task_a.stage_id, self.stage_done)
        self.assertEqual(self.task_a.state, "1_done")
        self.assertIn("MS typed", self.task_a.description)

    def test_cannot_edit_a_task_not_given(self):
        self._grant(self.task_a, self.user_x)
        with self.assertRaises(AccessError):
            self.task_b.with_user(self.user_x).write({"name": "MS Stolen"})

    def test_cannot_touch_fields_core_keeps_from_portal(self):
        self._grant(self.task_a, self.user_x)
        task = self.task_a.with_user(self.user_x)
        for vals in ({"project_id": self.project_2.id},
                     {"user_ids": [(6, 0, [])]},
                     {"ms_portal_partner_ids": [(4, self.user_y.partner_id.id)]}):
            with self.assertRaises(AccessError):
                task.write(vals)

    def _board_create(self, user):
        return self.env["project.task"].with_user(user).with_context(
            default_project_id=self.project.id).create({"name": "MS From The Board"})

    def test_one_task_user_creating_a_task(self):
        """What the New button on the board does, for someone given one task."""
        self._grant(self.task_a, self.user_x)
        with self.assertRaises(AccessError):
            self._board_create(self.user_x)

    def test_full_collaborator_creates_tasks(self):
        self.project._add_collaborators(self.user_x.partner_id)
        self.project.message_subscribe(partner_ids=self.user_x.partner_id.ids)
        self.assertEqual(self._board_create(self.user_x).project_id, self.project)

    def test_cannot_read_who_else_has_access(self):
        self._grant(self.task_a, self.user_x)
        with self.assertRaises(AccessError):
            self.task_a.with_user(self.user_x).read(["ms_portal_partner_ids"])

    # --- the two ways core leaks, closed for the flagged company --------------

    def test_a_new_task_does_not_reach_a_limited_user(self):
        self._grant(self.task_a, self.user_x)
        new_task = self._task("MS New Task")
        self.assertNotIn(self.user_x.partner_id, new_task.message_partner_ids)
        self.assertFalse(self._visible(self.user_x, new_task))

    def test_a_task_moved_in_does_not_reach_a_limited_user(self):
        self._grant(self.task_a, self.user_x)
        moved = self._task("MS Moved In", project=self.project_2)
        moved.project_id = self.project
        self.assertFalse(self._visible(self.user_x, moved))

    def test_a_colleague_of_the_same_customer_sees_nothing(self):
        self._grant(self.task_a, self.user_x)
        self.assertFalse(self._visible(self.user_colleague, self.task_a))
        self.assertFalse(self.env["project.project"].with_user(self.user_colleague).search(
            [("id", "=", self.project.id)]))

    # --- taking access away ---------------------------------------------------

    def test_revoke_keeps_the_project_while_another_task_is_given(self):
        self._grant(self.task_a, self.user_x)
        self._grant(self.task_b, self.user_x)
        self.task_a.ms_portal_partner_ids -= self.user_x.partner_id
        self.assertEqual(self._visible(self.user_x, self.task_a, self.task_b), self.task_b)
        self.assertTrue(self.project.with_user(self.user_x)._check_project_sharing_access())

    def test_revoking_the_last_task_leaves_the_project(self):
        self._grant(self.task_a, self.user_x)
        self.task_a.ms_portal_partner_ids -= self.user_x.partner_id
        self.assertFalse(self.project.collaborator_ids)
        self.assertNotIn(self.user_x.partner_id, self.project.message_partner_ids)
        self.assertFalse(self._visible(self.user_x, self.task_a))

    def test_removing_the_follower_in_the_chatter_revokes(self):
        self._grant(self.task_a, self.user_x)
        self.task_a.message_unsubscribe(partner_ids=self.user_x.partner_id.ids)
        self.assertFalse(self.task_a.ms_portal_partner_ids)
        self.assertFalse(self.project.collaborator_ids)

    def test_deleting_the_task_releases_the_project(self):
        self._grant(self.task_a, self.user_x)
        self.task_a.unlink()
        self.assertFalse(self.project.collaborator_ids)

    def test_archived_task_is_hidden_and_keeps_the_grant(self):
        self._grant(self.task_a, self.user_x)
        self.task_a.active = False
        self.assertFalse(self._visible(self.user_x, self.task_a))
        self.assertTrue(self.task_a.ms_portal_partner_ids)

    def test_project_no_longer_shared_clears_the_grants(self):
        self._grant(self.task_a, self.user_x)
        self.project.privacy_visibility = "employees"
        self.assertFalse(self.task_a.ms_portal_partner_ids)
        self.assertFalse(self.project.collaborator_ids)

    def test_moving_a_task_moves_the_access(self):
        self._grant(self.task_a, self.user_x)
        self.task_a.project_id = self.project_2
        self.assertFalse(self.project.collaborator_ids)
        self.assertEqual(self.project_2.collaborator_ids.partner_id, self.user_x.partner_id)
        self.assertEqual(self._visible(self.user_x, self.task_a), self.task_a)

    # --- subtasks -------------------------------------------------------------

    def test_subtasks_follow_the_parent(self):
        existing = self._task("MS Sub Existing", parent_id=self.task_a.id)
        self._grant(self.task_a, self.user_x)
        created = self._task("MS Sub New", parent_id=self.task_a.id)
        self.assertEqual(self._visible(self.user_x, existing, created), existing | created)
        self.task_a.ms_portal_partner_ids -= self.user_x.partner_id
        self.assertFalse(self._visible(self.user_x, existing, created))
        self.assertFalse(self.project.collaborator_ids)

    # --- Odoo's Share Project keeps working -----------------------------------

    def _share(self, user, access_mode):
        wizard = self.env["project.share.wizard"].with_context(
            active_model="project.project", active_id=self.project.id).create({
                "collaborator_ids": [(0, 0, {
                    "partner_id": user.partner_id.id, "access_mode": access_mode, "send_invitation": False,
                })],
            })
        return wizard

    def test_share_project_edit_sees_every_task_and_new_ones(self):
        self._share(self.user_x, "edit")
        new_task = self._task("MS New Task")
        self.assertEqual(self._visible(self.user_x, self.task_a, self.task_b, new_task),
                         self.task_a | self.task_b | new_task)
        new_task.with_user(self.user_x).stage_id = self.stage_done

    def test_share_project_limited_is_now_actually_limited(self):
        self._share(self.user_x, "edit_limited")
        self.assertFalse(self._visible(self.user_x, self._task("MS New Task")))

    def test_removing_a_collaborator_in_share_project_clears_the_grants(self):
        self._grant(self.task_a, self.user_x)
        self.env["project.share.wizard"].with_context(
            active_model="project.project", active_id=self.project.id).create({"collaborator_ids": False})
        self.assertFalse(self.task_a.ms_portal_partner_ids)
        self.assertFalse(self.project.collaborator_ids)

    def test_a_full_collaborator_is_not_downgraded_by_a_revoke(self):
        self._share(self.user_x, "edit")
        self._grant(self.task_a, self.user_x)
        self.task_a.ms_portal_partner_ids -= self.user_x.partner_id
        self.assertEqual(self.project.collaborator_ids.partner_id, self.user_x.partner_id)
        self.assertFalse(self.project.collaborator_ids.limited_access)
        self.assertEqual(self._visible(self.user_x, self.task_a), self.task_a)

    def test_read_only_follower_still_reads_but_cannot_edit(self):
        self.project.message_subscribe(partner_ids=self.user_x.partner_id.ids)
        self.task_a.message_subscribe(partner_ids=self.user_x.partner_id.ids)
        self.assertEqual(self._visible(self.user_x, self.task_a, self.task_b), self.task_a)

    # --- nothing changes for anyone else --------------------------------------

    def test_internal_users_see_as_before(self):
        self._grant(self.task_a, self.user_x)
        self.assertEqual(self._visible(self.user_project, self.task_a, self.task_b), self.task_a | self.task_b)

    def test_another_company_rejects_the_field(self):
        task = self._task("MS Other Task", project=self.project_other)
        self.assertFalse(task.ms_portal_enabled)
        with self.assertRaises(ValidationError):
            task.ms_portal_partner_ids |= self.user_elsewhere.partner_id

    def test_another_company_keeps_the_customer_wide_access_of_core(self):
        task = self._task("MS Other Task", project=self.project_other)
        customer = self.env["res.partner"].create({"name": "MS Other Customer", "is_company": True})
        one = new_test_user(self.env, login="ms_other_one", groups="base.group_portal",
                            company_id=self.other.id, company_ids=[(6, 0, self.other.ids)])
        two = new_test_user(self.env, login="ms_other_two", groups="base.group_portal",
                            company_id=self.other.id, company_ids=[(6, 0, self.other.ids)])
        (one | two).partner_id.parent_id = customer
        task.message_subscribe(partner_ids=one.partner_id.ids)
        self.assertEqual(self._visible(two, task), task, "core's behaviour must stay outside the flag")

    def test_another_company_keeps_core_auto_follow(self):
        self.project_other._add_collaborators(self.user_elsewhere.partner_id, limited_access=True)
        self.project_other.message_subscribe(partner_ids=self.user_elsewhere.partner_id.ids)
        task = self._task("MS Other New", project=self.project_other)
        self.assertIn(self.user_elsewhere.partner_id, task.message_partner_ids)

    def test_field_adds_no_dependency_on_users(self):
        """A domain on the field itself makes every change to a user search the
        tasks, which flushed new users too early and broke creating them."""
        self.assertFalse(self.env["project.task"]._fields["ms_portal_partner_ids"].domain)
        new_test_user(self.env, login="ms_portal_inbox", groups="base.group_user,base.group_partner_manager",
                      notification_type="inbox")

    # --- views ----------------------------------------------------------------

    def _form_arch(self, xmlid, user):
        view = self.env.ref(xmlid)
        return etree.fromstring(self.env["project.task"].with_user(user).get_view(view.id, "form")["arch"])

    def test_field_is_on_the_internal_form_only(self):
        arch = self._form_arch("project.view_task_form2", self.user_project)
        field = arch.xpath("//field[@name='ms_portal_partner_ids']")
        self.assertTrue(field)
        self.assertIn("not ms_portal_enabled", field[0].get("invisible"))
        sharing = self._form_arch("project.project_sharing_project_task_view_form", self.user_project)
        self.assertFalse(sharing.xpath("//field[@name='ms_portal_partner_ids']"))


@tagged("post_install", "-at_install")
class TestPortalTaskBoard(MsPortalCommon, HttpCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls._setup_data()

    def test_board_url_only_opens_for_someone_on_the_project(self):
        self.task_a.ms_portal_partner_ids |= self.user_x.partner_id
        url = "/my/projects/%d/project_sharing" % self.project.id
        self.authenticate(self.user_x.login, self.user_x.login)
        self.assertEqual(self.url_open(url).status_code, 200)
        self.authenticate(self.user_colleague.login, self.user_colleague.login)
        self.assertEqual(self.url_open(url).status_code, 403)

    def _post(self, task, project, body):
        return self.url_open("/mail/message/post", data=json.dumps({"params": {
            "thread_model": "project.task",
            "thread_id": task.id,
            "post_data": {"body": body, "message_type": "comment", "subtype_xmlid": "mail.mt_comment"},
            "project_sharing_id": project.id,
        }}), headers={"Content-Type": "application/json"}).json()

    def _posted(self, task, body):
        task.invalidate_recordset(["message_ids"])
        return any(body in (message.body or "") for message in task.message_ids)

    def test_chatter_is_limited_to_the_task_given(self):
        self.task_a.ms_portal_partner_ids |= self.user_x.partner_id
        self.authenticate(self.user_x.login, self.user_x.login)
        self._post(self.task_a, self.project, "MS allowed post")
        self.assertTrue(self._posted(self.task_a, "MS allowed post"))
        self._post(self.task_b, self.project, "MS refused post")
        self.assertFalse(self._posted(self.task_b, "MS refused post"))

    def test_chatter_stays_as_core_outside_the_flag(self):
        """The control: core takes this post, which is why the override exists."""
        project = self.project_other
        project._add_collaborators(self.user_elsewhere.partner_id, limited_access=True)
        project.message_subscribe(partner_ids=self.user_elsewhere.partner_id.ids)
        task = self._task("MS Other Task", project=project)
        task.message_unsubscribe(partner_ids=self.user_elsewhere.partner_id.ids)
        self.authenticate(self.user_elsewhere.login, self.user_elsewhere.login)
        self._post(task, project, "MS core post")
        self.assertTrue(self._posted(task, "MS core post"))

    def test_portal_lists_show_only_what_was_given(self):
        self.task_a.ms_portal_partner_ids |= self.user_x.partner_id
        self.authenticate(self.user_x.login, self.user_x.login)
        page = self.url_open("/my/tasks").text
        self.assertIn("MS Granted Task", page)
        self.assertNotIn("MS Hidden Task", page)
        self.assertIn("MS Portal Project", self.url_open("/my/projects").text)

    def test_portal_user_works_the_task_on_the_real_board(self):
        self.task_a.ms_portal_partner_ids |= self.user_x.partner_id
        self.task_b.ms_portal_partner_ids |= self.user_y.partner_id
        self.start_tour("/my/projects/%d/project_sharing" % self.project.id,
                        "ms_portal_task_board", login=self.user_x.login)
        self.assertEqual(self.task_a.name, "MS Renamed Task")
        self.assertEqual(self.task_a.stage_id, self.stage_done)
