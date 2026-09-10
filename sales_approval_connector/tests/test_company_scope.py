# -*- coding: utf-8 -*-
from lxml import etree
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestSaleApprovalCompanyScope(TransactionCase):
    """Approval configured for one company must not reach the others."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.env["res.company"].create({"name": "MS Appr Sale Co A"})
        cls.company_b = cls.env["res.company"].create({"name": "MS Appr Sale Co B"})
        # allowed_company_ids only narrows to companies the user belongs to.
        cls.env.user.company_ids = [(4, cls.company_a.id), (4, cls.company_b.id)]

        # Approvers act on the order itself (chatter, state, confirm) as
        # themselves, so they need access to it. A salesperson restricted to
        # their own documents cannot approve a colleague's order.
        cls.approver_a = cls.env["res.users"].create({
            "name": "MS Sale Approver A", "login": "ms_sale_approver_a",
            "company_id": cls.company_a.id,
            "company_ids": [(6, 0, [cls.company_a.id])],
            "group_ids": [(6, 0, [cls.env.ref("base.group_user").id,
                                  cls.env.ref("sales_team.group_sale_manager").id])],
        })
        cls.approver_b = cls.env["res.users"].create({
            "name": "MS Sale Approver B", "login": "ms_sale_approver_b",
            "company_id": cls.company_b.id,
            "company_ids": [(6, 0, [cls.company_b.id])],
            "group_ids": [(6, 0, [cls.env.ref("base.group_user").id,
                                  cls.env.ref("sales_team.group_sale_manager").id])],
        })

        cls.partner = cls.env["res.partner"].create({"name": "MS Appr Sale Customer"})
        cls.product = cls.env["product.product"].create(
            {"name": "MS Appr Sale Service", "type": "service"})

        cls.category_a = cls._make_category(cls.company_a, cls.approver_a, "A")

    @classmethod
    def _make_category(cls, company, approver, suffix, sequence=90):
        vals = {
            "name": "MS Sale Approval %s" % suffix,
            "approval_type": "sale",
            "company_id": company.id,
            "sequence": sequence,
            "has_product": "required",
            "has_quantity": "required",
        }
        if approver:
            vals["approver_ids"] = [(0, 0, {"user_id": approver.id, "required": True})]
        return cls.env["approval.category"].create(vals)

    def _order(self, company):
        return self.env["sale.order"].with_company(company).create({
            "company_id": company.id,
            "partner_id": self.partner.id,
            "order_line": [(0, 0, {"product_id": self.product.id, "product_uom_qty": 1,
                                   "price_unit": 100.0})],
        })

    # --- the requirement -----------------------------------------------------

    def test_configured_company_is_gated(self):
        order = self._order(self.company_a)
        order.action_confirm()
        self.assertEqual(order.state, "approve",
                         "an order of the configured company must wait for approval")
        request = self.env["approval.request"].search([("order_id", "=", order.id)])
        self.assertEqual(len(request), 1)
        self.assertEqual(request.approver_ids.user_id, self.approver_a)

    def test_other_company_confirms_normally(self):
        """The whole point: company B has no approval configured."""
        order = self._order(self.company_b)
        order.action_confirm()
        self.assertEqual(order.state, "sale",
                         "a company with no approval configured must confirm straight through")
        self.assertFalse(self.env["approval.request"].search([("order_id", "=", order.id)]))

    def test_scope_ignores_the_company_switcher(self):
        """A company B order stays ungated even when A is also active."""
        both = [self.company_a.id, self.company_b.id]
        order = self._order(self.company_b).with_context(allowed_company_ids=both)
        order.action_confirm()
        self.assertEqual(order.state, "sale")

    def test_each_company_keeps_its_own_approver(self):
        self._make_category(self.company_b, self.approver_b, "B")
        order_a = self._order(self.company_a)
        order_b = self._order(self.company_b)
        (order_a | order_b).action_confirm()

        request_a = self.env["approval.request"].search([("order_id", "=", order_a.id)])
        request_b = self.env["approval.request"].search([("order_id", "=", order_b.id)])
        self.assertEqual(request_a.approver_ids.user_id, self.approver_a)
        self.assertEqual(request_b.approver_ids.user_id, self.approver_b,
                         "company B's order must go to company B's approver")

    # --- categories that must be ignored -------------------------------------

    def test_category_without_approvers_is_ignored(self):
        """An unconfigured category must not park the order in To Approve."""
        self._make_category(self.company_b, None, "B empty")
        order = self._order(self.company_b)
        order.action_confirm()
        self.assertEqual(order.state, "sale",
                         "a category with no approvers means no approval is set up")

    def test_empty_lower_sequence_category_does_not_hijack(self):
        """Mirrors Odoo's own empty category sorting ahead of the real one."""
        self._make_category(self.company_a, None, "A empty", sequence=10)
        order = self._order(self.company_a)
        order.action_confirm()
        self.assertEqual(order.state, "approve",
                         "the configured category must still win over an empty one")
        request = self.env["approval.request"].search([("order_id", "=", order.id)])
        self.assertEqual(request.category_id, self.category_a)

    # --- the approval itself still works -------------------------------------

    def test_approving_confirms_the_order(self):
        order = self._order(self.company_a)
        order.action_confirm()
        request = self.env["approval.request"].search([("order_id", "=", order.id)])
        request.with_user(self.approver_a).action_approve()
        self.assertEqual(order.state, "sale", "approval must confirm the order")
        self.assertTrue(order.is_approved)

    # --- the rest of the cycle ------------------------------------------------

    def test_refusing_cancels_the_order(self):
        order = self._order(self.company_a)
        order.action_confirm()
        request = self.env["approval.request"].search([("order_id", "=", order.id)])
        request.with_user(self.approver_a).action_refuse()
        self.assertEqual(order.state, "cancel", "a refusal must cancel the order")

    def test_reset_to_draft_and_resubmit(self):
        """The historically broken path: refuse, reset, submit again."""
        order = self._order(self.company_a)
        order.action_confirm()
        first = self.env["approval.request"].search([("order_id", "=", order.id)])
        first.with_user(self.approver_a).action_refuse()

        order.action_draft()
        self.assertEqual(order.state, "draft")
        self.assertFalse(order.is_approved)
        self.assertFalse(self.env["approval.request"].search([("order_id", "=", order.id)]),
                         "the dead request must not linger and capture the buttons")

        order.action_confirm()
        second = self.env["approval.request"].search([("order_id", "=", order.id)])
        self.assertEqual(len(second), 1, "resubmitting must raise exactly one fresh request")
        self.assertEqual(order.state, "approve")
        second.with_user(self.approver_a).action_approve()
        self.assertEqual(order.state, "sale")

    def test_approver_sees_the_approve_button(self):
        order = self._order(self.company_a)
        order.action_confirm()
        self.assertTrue(order.with_user(self.approver_a).is_approval_allowed,
                        "the pending approver must be offered the button")
        other = self.env["res.users"].create({
            "name": "MS Sale Bystander", "login": "ms_sale_bystander",
            "company_id": self.company_a.id,
            "company_ids": [(6, 0, [self.company_a.id])],
            "group_ids": [(6, 0, [self.env.ref("sales_team.group_sale_manager").id])],
        })
        self.assertFalse(order.with_user(other).is_approval_allowed,
                         "a non-approver must not be offered the button")

    # --- which confirm button the form offers ---------------------------------

    def test_flag_is_false_when_no_approval_is_configured(self):
        """Drives the button: no approval for this company -> plain Confirm."""
        self.assertTrue(self._order(self.company_a).is_approval_required)
        self.assertFalse(self._order(self.company_b).is_approval_required)

    def test_flag_follows_the_company_on_the_record(self):
        order = self._order(self.company_b)
        self.assertFalse(order.is_approval_required)
        order.company_id = self.company_a
        order.invalidate_recordset(["is_approval_required"])
        self.assertTrue(order.is_approval_required,
                        "switching the order to a configured company must flip the flag")

    def test_both_confirm_buttons_are_gated_on_the_flag(self):
        """The submit button and Odoo's own confirm must be mutually exclusive."""
        view = self.env.ref("sale.view_order_form")
        arch = etree.fromstring(
            self.env["sale.order"].get_view(view_id=view.id, view_type="form")["arch"])

        submit = arch.xpath("//header/button[@string='Submit for Approval']")
        self.assertTrue(submit, "the Submit for Approval button is missing")
        self.assertIn("not is_approval_required", submit[0].get("invisible"))

        plain = [b for b in arch.xpath("//header/button[@name='action_confirm']")
                 if b.get("invisible") and "is_approval_required" in b.get("invisible")
                 and "not is_approval_required" not in b.get("invisible")]
        self.assertTrue(plain,
                        "no standard confirm button is offered when approval is not configured")
