# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestCrmOwnLeads(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        group_own_leads = cls.env.ref("ms_customization.group_crm_own_leads_only")
        group_sale_manager = cls.env.ref("sales_team.group_sale_manager")
        group_user = cls.env.ref("base.group_user")

        cls.user_a = cls.env["res.users"].create({
            "name": "Sales Person A",
            "login": "user_a@rajacompany.com",
            "email": "user_a@rajacompany.com",
            "group_ids": [(6, 0, [group_user.id, group_sale_manager.id, group_own_leads.id])],
        })

        cls.user_b = cls.env["res.users"].create({
            "name": "Sales Person B",
            "login": "user_b@rajacompany.com",
            "email": "user_b@rajacompany.com",
            "group_ids": [(6, 0, [group_user.id, group_sale_manager.id, group_own_leads.id])],
        })

        cls.user_unrestricted = cls.env["res.users"].create({
            "name": "Unrestricted Sales Manager",
            "login": "unrestricted@rajacompany.com",
            "email": "unrestricted@rajacompany.com",
            "group_ids": [(6, 0, [group_user.id, group_sale_manager.id])],
        })

        cls.lead_a = cls.env["crm.lead"].create({
            "name": "Lead A",
            "user_id": cls.user_a.id,
        })
        cls.lead_b = cls.env["crm.lead"].create({
            "name": "Lead B",
            "user_id": cls.user_b.id,
        })
        cls.lead_unassigned = cls.env["crm.lead"].create({
            "name": "Unassigned Lead",
            "user_id": False,
        })

    def test_user_a_sees_only_own_leads(self):
        """User A sees only Lead A; Lead B and Unassigned leads are hidden."""
        leads = self.env["crm.lead"].with_user(self.user_a).search([
            ("id", "in", [self.lead_a.id, self.lead_b.id, self.lead_unassigned.id])
        ])
        self.assertIn(self.lead_a, leads)
        self.assertNotIn(self.lead_b, leads)
        self.assertNotIn(self.lead_unassigned, leads)

    def test_user_b_sees_only_own_leads(self):
        """User B sees only Lead B; Lead A and Unassigned leads are hidden."""
        leads = self.env["crm.lead"].with_user(self.user_b).search([
            ("id", "in", [self.lead_a.id, self.lead_b.id, self.lead_unassigned.id])
        ])
        self.assertIn(self.lead_b, leads)
        self.assertNotIn(self.lead_a, leads)
        self.assertNotIn(self.lead_unassigned, leads)

    def test_unrestricted_user_sees_all_leads(self):
        """An unrestricted user sees all leads including unassigned ones."""
        leads = self.env["crm.lead"].with_user(self.user_unrestricted).search([
            ("id", "in", [self.lead_a.id, self.lead_b.id, self.lead_unassigned.id])
        ])
        self.assertIn(self.lead_a, leads)
        self.assertIn(self.lead_b, leads)
        self.assertIn(self.lead_unassigned, leads)

    def test_sales_orders_unaffected_by_crm_rule(self):
        """Sales Orders remain accessible to Sales Managers despite CRM lead restriction."""
        partner = self.env["res.partner"].create({"name": "Test Customer"})
        so_b = self.env["sale.order"].with_user(self.user_b).create({
            "partner_id": partner.id,
            "user_id": self.user_b.id,
        })
        orders = self.env["sale.order"].with_user(self.user_a).search([("id", "=", so_b.id)])
        self.assertIn(so_b, orders)
