# -*- coding: utf-8 -*-
from odoo.tests import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestPettyBulkApprove(HttpCase):
    """Bulk approval from the list view must approve only the vouchers the
    current user is actually authorised to approve (same rules as the single
    action_approve), and skip the rest."""

    def _isolate_and_build(self):
        env = self.env
        company = env.ref("base.user_admin").company_id

        # Deterministic environment: disable any pre-existing policies and
        # approval-matrix rules, then install a single known rule.
        env["dev.petty.policy"].search([]).write({"active": False})
        env["dev.petty.approval.matrix"].search([]).write({"active": False})

        approver_group = env["res.groups"].create({"name": "TEST Petty Approver"})
        env["dev.petty.approval.matrix"].create({
            "name": "TEST Rule",
            "sequence": 1,
            "company_id": company.id,
            "min_amount": 0.0,
            "max_amount": 0.0,  # 0 = unlimited upper bound
            "approver_group_id": approver_group.id,
            "auto_approve": False,
        })

        internal = env.ref("base.group_user")
        manager_group = env.ref("dev_petty_cash.group_petty_manager")
        approver_user = env["res.users"].create({
            "name": "Bulk Approver",
            "login": "bulk_approver",
            "password": "bulk_approver",
            "company_id": company.id,
            "company_ids": [(6, 0, [company.id])],
            "group_ids": [(4, internal.id), (4, manager_group.id), (4, approver_group.id)],
        })
        other_user = env["res.users"].create({
            "name": "Bulk NonApprover",
            "login": "bulk_other",
            "password": "bulk_other",
            "company_id": company.id,
            "company_ids": [(6, 0, [company.id])],
            "group_ids": [(4, internal.id), (4, manager_group.id)],  # manager, but NOT an approver
        })

        journal = env["account.journal"].search(
            [("type", "in", ("cash", "bank")), ("company_id", "=", company.id)], limit=1)
        self.assertTrue(journal, "need a cash/bank journal")
        account = env["account.account"].search(
            [("account_type", "=", "expense"), ("company_ids", "in", company.id)], limit=1)
        self.assertTrue(account, "need an expense account")
        fund = env["dev.petty.fund"].create({
            "name": "Bulk Test Fund",
            "company_id": company.id,
            "currency_id": company.currency_id.id,
            "journal_id": journal.id,
            "float_amount": 1000.0,
            "responsible_user_id": approver_user.id,
        })
        return company, approver_user, other_user, approver_group, fund, account

    def _make_requested_voucher(self, fund, account, company):
        voucher = self.env["dev.petty.voucher"].create({
            "fund_id": fund.id,
            "company_id": company.id,
            "requester_id": self.env.ref("base.user_admin").id,
            "purpose": "Bulk approve test",
            "line_ids": [(0, 0, {
                "description": "Item",
                "quantity": 1.0,
                "price_unit": 10.0,
                "account_id": account.id,
            })],
        })
        voucher.action_request()
        self.assertEqual(voucher.state, "requested")
        return voucher

    def test_bulk_approve_permissions(self):
        company, approver_user, other_user, approver_group, fund, account = self._isolate_and_build()
        v1 = self._make_requested_voucher(fund, account, company)
        v2 = self._make_requested_voucher(fund, account, company)
        vouchers = v1 | v2

        # A manager who is NOT in the approver group approves nothing.
        vouchers.with_user(other_user).action_approve_selected()
        self.assertEqual(v1.state, "requested", "non-approver must not approve")
        self.assertEqual(v2.state, "requested", "non-approver must not approve")

        # The approver approves both at once.
        vouchers.with_user(approver_user).action_approve_selected()
        self.assertEqual(v1.state, "approved")
        self.assertEqual(v2.state, "approved")

    def test_bulk_approve_tour(self):
        company, approver_user, other_user, approver_group, fund, account = self._isolate_and_build()
        # Let admin (the tour login) be an approver.
        self.env.ref("base.user_admin").group_ids |= approver_group
        self._make_requested_voucher(fund, account, company)
        self._make_requested_voucher(fund, account, company)

        self.start_tour("/odoo", "petty_bulk_approve_tour", login="admin")
