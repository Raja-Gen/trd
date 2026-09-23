# -*- coding: utf-8 -*-
from lxml import etree

from odoo.tests.common import TransactionCase, tagged

RAJA_NAME = "RAJA INTERNATIONAL GENERAL TRADING (LLC)"


@tagged("post_install", "-at_install")
class TestCrmInventoryItemsScope(TransactionCase):
    """The Inventory Items tab and its quotation sync are Raja-only."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Company = cls.env["res.company"]
        cls.raja = Company.search([("name", "=", RAJA_NAME)], limit=1) \
            or Company.create({"name": RAJA_NAME})
        cls.other = Company.create({"name": "MS CRM Not Raja"})
        cls.env.user.company_ids = [(4, cls.raja.id), (4, cls.other.id)]

        cls.partner = cls.env["res.partner"].create({"name": "MS CRM Customer"})
        cls.product = cls.env["product.product"].create(
            {"name": "MS CRM Item", "is_storable": True})

    def _lead(self, company):
        lead = self.env["crm.lead"].with_company(company).create({
            "name": "MS CRM Opportunity",
            "type": "opportunity",
            "company_id": company.id,
            "partner_id": self.partner.id,
        })
        lead.lead_product_line_ids = [(0, 0, {
            "product_id": self.product.id, "product_uom_qty": 3.0})]
        return lead

    def _quotation(self, lead):
        return self.env["sale.order"].with_company(lead.company_id).create({
            "company_id": lead.company_id.id,
            "partner_id": self.partner.id,
            "opportunity_id": lead.id,
        })

    # --- the flag -------------------------------------------------------------

    def test_flag_follows_the_lead_company(self):
        self.assertTrue(self._lead(self.raja).ms_is_raja_company)
        self.assertFalse(self._lead(self.other).ms_is_raja_company)

    # --- the tab --------------------------------------------------------------

    def test_tab_is_hidden_outside_the_raja_companies(self):
        view = self.env.ref("crm.crm_lead_view_form")
        arch = etree.fromstring(
            self.env["crm.lead"].get_view(view_id=view.id, view_type="form")["arch"])
        pages = arch.xpath("//page[@name='ms_inventory_items']")
        self.assertTrue(pages, "the Inventory Items tab is missing")
        self.assertIn("not ms_is_raja_company", pages[0].get("invisible") or "",
                      "the tab must be hidden for other companies")

    # --- the quotation sync ---------------------------------------------------

    def test_sync_fills_a_raja_quotation(self):
        lead = self._lead(self.raja)
        order = self._quotation(lead)
        self.assertEqual(len(order.order_line), 1, "the lead's items must carry over")
        self.assertEqual(order.order_line.product_id, self.product)
        self.assertEqual(order.order_line.product_uom_qty, 3.0)

    def test_sync_does_not_run_for_another_company(self):
        lead = self._lead(self.other)
        self.assertTrue(lead.lead_product_line_ids, "the lead still holds its items")
        order = self._quotation(lead)
        self.assertFalse(order.order_line,
                         "a non-Raja quotation must not be filled from the lead")

    def test_helper_returns_nothing_outside_raja(self):
        lead = self._lead(self.other)
        order = self._quotation(lead)
        self.assertEqual(order._ms_prepare_lines_from_lead(), [])

    def test_existing_lines_are_still_never_overwritten(self):
        """The original guard must survive the new one."""
        lead = self._lead(self.raja)
        other_product = self.env["product.product"].create(
            {"name": "MS CRM Keyed In", "is_storable": True})
        order = self.env["sale.order"].with_company(self.raja).create({
            "company_id": self.raja.id,
            "partner_id": self.partner.id,
            "opportunity_id": lead.id,
            "order_line": [(0, 0, {"product_id": other_product.id, "product_uom_qty": 1})],
        })
        self.assertEqual(order.order_line.product_id, other_product,
                         "hand-keyed lines must survive")
