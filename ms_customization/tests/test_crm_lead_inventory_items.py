# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestCrmLeadInventoryItems(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Test Customer"})
        cls.product = cls.env["product.product"].create({
            "name": "Safety Helmet",
            "is_storable": True,
        })
        cls.lead = cls.env["crm.lead"].create({
            "name": "Test Lead with Inventory",
            "type": "opportunity",
            "partner_id": cls.partner.id,
        })

    def test_lead_product_line_creation(self):
        """Adding inventory items to lead computes count and stock status fields."""
        line = self.env["crm.lead.product.line"].create({
            "lead_id": self.lead.id,
            "product_id": self.product.id,
            "product_uom_qty": 5.0,
        })
        self.assertEqual(self.lead.lead_product_count, 1)
        self.assertEqual(line.product_uom_id, self.product.uom_id)

    def test_availability_status_computation(self):
        """Test availability status badge values based on free stock vs requested quantity."""
        line = self.env["crm.lead.product.line"].create({
            "lead_id": self.lead.id,
            "product_id": self.product.id,
            "product_uom_qty": 10.0,
        })
        self.assertEqual(line._get_availability_status(free_qty=15.0), "available")
        self.assertEqual(line._get_availability_status(free_qty=5.0), "partial")
        self.assertEqual(line._get_availability_status(free_qty=0.0), "unavailable")

    def test_prefill_quotation_lines_from_lead(self):
        """Creating a quotation pre-fills sale order lines from the lead's inventory items."""
        self.env["crm.lead.product.line"].create({
            "lead_id": self.lead.id,
            "product_id": self.product.id,
            "product_uom_qty": 20.0,
        })
        so = self.env["sale.order"].create({
            "partner_id": self.partner.id,
            "opportunity_id": self.lead.id,
        })
        self.assertEqual(len(so.order_line), 1)
        self.assertEqual(so.order_line.product_id, self.product)
        self.assertEqual(so.order_line.product_uom_qty, 20.0)
