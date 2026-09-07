# -*- coding: utf-8 -*-
from lxml import etree

from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestCustomerType(TransactionCase):
    """Customer Type (Trader / End User) on res.partner."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Partner = cls.env["res.partner"]

    def _arch(self, xmlid):
        """The final arch of a view, as the web client would receive it."""
        view = self.env.ref(xmlid)
        return etree.fromstring(
            self.Partner.get_view(view_id=view.id, view_type=view.type)["arch"])

    # --- the field itself -----------------------------------------------------

    def test_field_offers_trader_and_end_user(self):
        field = self.Partner._fields["ms_customer_type"]
        self.assertEqual(
            dict(self.Partner.fields_get(["ms_customer_type"])
                 ["ms_customer_type"]["selection"]),
            {"trader": "Trader", "end_user": "End User"})
        self.assertFalse(field.required, "the type must stay optional")

    def test_type_is_optional_and_settable(self):
        partner = self.Partner.create({"name": "Unclassified Customer"})
        self.assertFalse(partner.ms_customer_type)

        partner.ms_customer_type = "trader"
        self.assertEqual(partner.ms_customer_type, "trader")
        partner.ms_customer_type = False
        self.assertFalse(partner.ms_customer_type, "the type must be clearable")

    def test_set_on_creation(self):
        partner = self.Partner.create(
            {"name": "New Customer", "ms_customer_type": "end_user"})
        self.assertEqual(partner.ms_customer_type, "end_user")

    def test_search_and_group_by(self):
        """Written relative to a baseline: the database may already hold either type."""
        trader_before = self.Partner.search_count([("ms_customer_type", "=", "trader")])
        end_user_before = self.Partner.search_count([("ms_customer_type", "=", "end_user")])

        self.Partner.create([
            {"name": "Test Trader A", "ms_customer_type": "trader"},
            {"name": "Test Trader B", "ms_customer_type": "trader"},
            {"name": "Test End User A", "ms_customer_type": "end_user"},
        ])

        self.assertEqual(
            self.Partner.search_count([("ms_customer_type", "=", "trader")]),
            trader_before + 2)
        self.assertEqual(
            self.Partner.search_count([("ms_customer_type", "=", "end_user")]),
            end_user_before + 1)

        groups = dict(self.Partner._read_group(
            [("name", "like", "Test Trader")], ["ms_customer_type"], ["__count"]))
        self.assertEqual(groups, {"trader": 2})

    def test_tracked_on_the_chatter(self):
        partner = self.Partner.create({"name": "Tracked Customer"})
        # Tracking values are only written out on precommit, and the messages are
        # read back off mail.message rather than partner.message_ids, which is
        # already cached by the time precommit creates them.
        self.env.cr.precommit.run()
        domain = [("model", "=", "res.partner"), ("res_id", "=", partner.id)]
        before = self.env["mail.message"].search_count(domain)

        partner.ms_customer_type = "trader"
        self.env.cr.precommit.run()

        messages = self.env["mail.message"].search(domain)
        self.assertEqual(
            len(messages), before + 1,
            "changing the customer type must be logged on the chatter")
        tracked = messages.tracking_value_ids.field_id.mapped("name")
        self.assertIn("ms_customer_type", tracked)

    # --- the views ------------------------------------------------------------

    def test_field_is_on_the_contact_form(self):
        arch = self._arch("base.view_partner_form")
        self.assertTrue(
            arch.xpath("//field[@name='ms_customer_type']"),
            "Customer Type is missing from the contact form")

    def test_field_is_on_the_quick_create_form(self):
        arch = self._arch("base.view_partner_simple_form")
        self.assertTrue(
            arch.xpath("//field[@name='ms_customer_type']"),
            "Customer Type is missing from the simplified contact form")

    def test_field_is_an_optional_column_on_the_list(self):
        arch = self._arch("base.view_partner_tree")
        nodes = arch.xpath("//field[@name='ms_customer_type']")
        self.assertTrue(nodes, "Customer Type is missing from the contact list")
        self.assertEqual(nodes[0].get("optional"), "hide")

    def test_search_filters_and_group_by_are_present(self):
        arch = self._arch("base.view_res_partner_filter")
        for name in ("ms_customer_type_trader", "ms_customer_type_end_user",
                     "ms_customer_type_unset", "group_ms_customer_type"):
            self.assertTrue(
                arch.xpath("//filter[@name='%s']" % name),
                "search view is missing the %s filter" % name)
