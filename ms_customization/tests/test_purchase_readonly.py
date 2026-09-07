# -*- coding: utf-8 -*-
from odoo.exceptions import AccessError
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestPurchaseReadOnly(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({"name": "Test Vendor"})
        cls.product = cls.env["product.product"].create({
            "name": "Test Product",
            "type": "consu",
            "standard_price": 100.0,
        })

        # Create a user with Purchase Read Only access
        cls.user_readonly = cls.env["res.users"].create({
            "name": "Purchase Read Only User",
            "login": "purchase_readonly_user",
            "email": "readonly@rajacompany.com",
            "group_ids": [(6, 0, [
                cls.env.ref("base.group_user").id,
                cls.env.ref("ms_customization.group_purchase_readonly").id,
            ])],
        })

        # Create a sample Purchase Order with admin
        cls.purchase_order = cls.env["purchase.order"].create({
            "partner_id": cls.partner.id,
            "order_line": [
                (0, 0, {
                    "product_id": cls.product.id,
                    "product_qty": 5.0,
                    "price_unit": 100.0,
                })
            ],
        })

    def test_read_purchase_order_allowed(self):
        """User with group_purchase_readonly can read purchase orders and lines."""
        po = self.purchase_order.with_user(self.user_readonly)
        self.assertEqual(po.name, self.purchase_order.name)
        self.assertEqual(len(po.order_line), 1)
        self.assertEqual(po.order_line.product_id, self.product)

    def test_create_purchase_order_access_error(self):
        """User with group_purchase_readonly cannot create a purchase order."""
        with self.assertRaises(AccessError):
            self.env["purchase.order"].with_user(self.user_readonly).create({
                "partner_id": self.partner.id,
            })

    def test_write_purchase_order_access_error(self):
        """User with group_purchase_readonly cannot edit a purchase order."""
        with self.assertRaises(AccessError):
            self.purchase_order.with_user(self.user_readonly).write({
                "notes": "Modifying PO",
            })

    def test_unlink_purchase_order_access_error(self):
        """User with group_purchase_readonly cannot delete a purchase order."""
        po = self.env["purchase.order"].create({"partner_id": self.partner.id})
        with self.assertRaises(AccessError):
            po.with_user(self.user_readonly).unlink()

    def test_vendor_bills_rule(self):
        """Vendor bills are accessible in read-only mode, but customer invoices are blocked."""
        vendor_bill = self.env["account.move"].create({
            "move_type": "in_invoice",
            "partner_id": self.partner.id,
        })
        customer_invoice = self.env["account.move"].create({
            "move_type": "out_invoice",
            "partner_id": self.partner.id,
        })

        moves = self.env["account.move"].with_user(self.user_readonly).search([
            ("id", "in", [vendor_bill.id, customer_invoice.id])
        ])
        self.assertIn(vendor_bill, moves)
        self.assertNotIn(customer_invoice, moves)
