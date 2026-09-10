# -*- coding: utf-8 -*-
from lxml import etree
from odoo import fields
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPurchaseApprovalCompanyScope(TransactionCase):
    """Approval configured for one company must not reach the others."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company_a = cls.env["res.company"].create({"name": "MS Appr Pur Co A"})
        cls.company_b = cls.env["res.company"].create({"name": "MS Appr Pur Co B"})
        cls.env.user.company_ids = [(4, cls.company_a.id), (4, cls.company_b.id)]

        cls.approver_a = cls.env["res.users"].create({
            "name": "MS Pur Approver A", "login": "ms_pur_approver_a",
            "company_id": cls.company_a.id,
            "company_ids": [(6, 0, [cls.company_a.id])],
            "group_ids": [(6, 0, [cls.env.ref("base.group_user").id,
                                  cls.env.ref("purchase.group_purchase_user").id])],
        })
        cls.approver_b = cls.env["res.users"].create({
            "name": "MS Pur Approver B", "login": "ms_pur_approver_b",
            "company_id": cls.company_b.id,
            "company_ids": [(6, 0, [cls.company_b.id])],
            "group_ids": [(6, 0, [cls.env.ref("base.group_user").id,
                                  cls.env.ref("purchase.group_purchase_user").id])],
        })

        cls.vendor = cls.env["res.partner"].create({"name": "MS Appr Pur Vendor"})
        cls.product = cls.env["product.product"].create(
            {"name": "MS Appr Pur Service", "type": "service", "purchase_ok": True})

        cls.category_a = cls._make_category(cls.company_a, cls.approver_a, "A")

    @classmethod
    def _make_category(cls, company, approver, suffix, sequence=90):
        vals = {
            "name": "MS Purchase Approval %s" % suffix,
            "approval_type": "purchase",
            "company_id": company.id,
            "sequence": sequence,
            "has_product": "required",
            "has_quantity": "required",
        }
        if approver:
            vals["approver_ids"] = [(0, 0, {"user_id": approver.id, "required": True})]
        return cls.env["approval.category"].create(vals)

    def _order(self, company):
        return self.env["purchase.order"].with_company(company).create({
            "company_id": company.id,
            "partner_id": self.vendor.id,
            "order_line": [(0, 0, {
                "product_id": self.product.id,
                "name": self.product.name,
                "product_qty": 1,
                "price_unit": 100.0,
                "date_planned": fields.Datetime.now(),
            })],
        })

    # --- the requirement -----------------------------------------------------

    def test_configured_company_is_gated(self):
        order = self._order(self.company_a)
        order.button_confirm()
        self.assertEqual(order.state, "to_approve",
                         "an order of the configured company must wait for approval")
        request = self.env["approval.request"].search([("purchase_order_id", "=", order.id)])
        self.assertEqual(len(request), 1)
        self.assertEqual(request.approver_ids.user_id, self.approver_a)

    def test_other_company_confirms_normally(self):
        order = self._order(self.company_b)
        order.button_confirm()
        self.assertEqual(order.state, "purchase",
                         "a company with no approval configured must confirm straight through")
        self.assertFalse(
            self.env["approval.request"].search([("purchase_order_id", "=", order.id)]))

    def test_scope_ignores_the_company_switcher(self):
        both = [self.company_a.id, self.company_b.id]
        order = self._order(self.company_b).with_context(allowed_company_ids=both)
        order.button_confirm()
        self.assertEqual(order.state, "purchase")

    def test_each_company_keeps_its_own_approver(self):
        self._make_category(self.company_b, self.approver_b, "B")
        order_a = self._order(self.company_a)
        order_b = self._order(self.company_b)
        (order_a | order_b).button_confirm()

        request_a = self.env["approval.request"].search([("purchase_order_id", "=", order_a.id)])
        request_b = self.env["approval.request"].search([("purchase_order_id", "=", order_b.id)])
        self.assertEqual(request_a.approver_ids.user_id, self.approver_a)
        self.assertEqual(request_b.approver_ids.user_id, self.approver_b,
                         "company B's order must go to company B's approver")

    # --- categories that must be ignored -------------------------------------

    def test_category_without_approvers_is_ignored(self):
        self._make_category(self.company_b, None, "B empty")
        order = self._order(self.company_b)
        order.button_confirm()
        self.assertEqual(order.state, "purchase",
                         "a category with no approvers means no approval is set up")

    def test_odoos_own_empty_rfq_category_does_not_hijack(self):
        """approvals_purchase ships 'Create RFQ's' at sequence 80 with no
        approvers; it must never win the lookup."""
        self._make_category(self.company_a, None, "A empty", sequence=10)
        order = self._order(self.company_a)
        order.button_confirm()
        self.assertEqual(order.state, "to_approve",
                         "the configured category must still win over an empty one")
        request = self.env["approval.request"].search([("purchase_order_id", "=", order.id)])
        self.assertEqual(request.category_id, self.category_a)

    # --- the approval itself still works -------------------------------------

    def test_approving_confirms_the_order(self):
        order = self._order(self.company_a)
        order.button_confirm()
        request = self.env["approval.request"].search([("purchase_order_id", "=", order.id)])
        request.with_user(self.approver_a).action_approve()
        self.assertEqual(order.state, "purchase", "approval must confirm the order")
        self.assertTrue(order.is_approved)

    # --- the rest of the cycle ------------------------------------------------

    def test_refusing_cancels_the_order(self):
        order = self._order(self.company_a)
        order.button_confirm()
        request = self.env["approval.request"].search([("purchase_order_id", "=", order.id)])
        request.with_user(self.approver_a).action_refuse()
        self.assertEqual(order.state, "cancel", "a refusal must cancel the order")

    def test_reset_to_draft_and_resubmit(self):
        """The historically broken path: refuse, reset, submit again."""
        order = self._order(self.company_a)
        order.button_confirm()
        first = self.env["approval.request"].search([("purchase_order_id", "=", order.id)])
        first.with_user(self.approver_a).action_refuse()

        order.button_draft()
        self.assertEqual(order.state, "draft")
        self.assertFalse(order.is_approved)
        self.assertFalse(
            self.env["approval.request"].search([("purchase_order_id", "=", order.id)]),
            "the dead request must not linger and capture the buttons")

        order.button_confirm()
        second = self.env["approval.request"].search([("purchase_order_id", "=", order.id)])
        self.assertEqual(len(second), 1, "resubmitting must raise exactly one fresh request")
        self.assertEqual(order.state, "to_approve")
        second.with_user(self.approver_a).action_approve()
        self.assertEqual(order.state, "purchase")

    def test_approver_sees_the_approve_button(self):
        order = self._order(self.company_a)
        order.button_confirm()
        self.assertTrue(order.with_user(self.approver_a).is_approval_allowed)

    # --- high-value escalation (the module's own feature) ---------------------

    def test_high_value_order_needs_the_final_approver(self):
        final = self.env["res.users"].create({
            "name": "MS Pur Final Approver", "login": "ms_pur_final_approver",
            "company_id": self.company_a.id,
            "company_ids": [(6, 0, [self.company_a.id])],
            "group_ids": [(6, 0, [self.env.ref("base.group_user").id,
                                  self.env.ref("purchase.group_purchase_manager").id])],
        })
        self.category_a.write({
            "po_approval_threshold": 500.0,
            "po_final_approver_id": final.id,
        })
        order = self._order(self.company_a)
        order.order_line.price_unit = 5000.0        # well over the threshold
        order.button_confirm()
        request = self.env["approval.request"].search([("purchase_order_id", "=", order.id)])

        request.with_user(self.approver_a).action_approve()
        self.assertEqual(order.state, "to_approve",
                         "over the threshold the order must wait for the final approver")
        self.assertIn(final, request.approver_ids.user_id,
                      "the final approver must have been added to the chain")

        request.with_user(final).action_approve()
        self.assertEqual(order.state, "purchase",
                         "once the final approver signs, the order confirms")

    def test_low_value_order_skips_the_final_approver(self):
        final = self.env["res.users"].create({
            "name": "MS Pur Final Approver 2", "login": "ms_pur_final_approver_2",
            "company_id": self.company_a.id,
            "company_ids": [(6, 0, [self.company_a.id])],
            "group_ids": [(6, 0, [self.env.ref("base.group_user").id,
                                  self.env.ref("purchase.group_purchase_manager").id])],
        })
        self.category_a.write({
            "po_approval_threshold": 100000.0,
            "po_final_approver_id": final.id,
        })
        order = self._order(self.company_a)      # 100.0, far below the threshold
        order.button_confirm()
        request = self.env["approval.request"].search([("purchase_order_id", "=", order.id)])
        request.with_user(self.approver_a).action_approve()
        self.assertEqual(order.state, "purchase",
                         "under the threshold the normal chain is enough")
        self.assertNotIn(final, request.approver_ids.user_id)

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
        view = self.env.ref("purchase.purchase_order_form")
        arch = etree.fromstring(
            self.env["purchase.order"].get_view(view_id=view.id, view_type="form")["arch"])

        submit = arch.xpath("//header/button[@string='Submit for Approval']")
        self.assertTrue(submit, "the Submit for Approval button is missing")
        self.assertIn("not is_approval_required", submit[0].get("invisible"))

        plain = [b for b in arch.xpath("//header/button[@name='button_confirm']")
                 if b.get("invisible") and "is_approval_required" in b.get("invisible")
                 and "not is_approval_required" not in b.get("invisible")]
        self.assertTrue(plain,
                        "no standard confirm button is offered when approval is not configured")
