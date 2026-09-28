# -*- coding: utf-8 -*-
import re

from odoo.tests.common import TransactionCase, tagged

RAJA_NAME = "RAJA INTERNATIONAL GENERAL TRADING (LLC)"


@tagged("post_install", "-at_install")
class TestSaleReportDecimals(TransactionCase):
    """Quantity and Unit Price print with 2 decimals for the Raja companies only."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Company = cls.env["res.company"]
        cls.raja = Company.search([("name", "=", RAJA_NAME)], limit=1) \
            or Company.create({"name": RAJA_NAME})
        cls.other = Company.create({"name": "MS Decimals Not Raja"})
        cls.env.user.company_ids = [(4, cls.raja.id), (4, cls.other.id)]

        cls.partner = cls.env["res.partner"].create({"name": "MS Decimals Customer"})
        cls.product = cls.env["product.product"].create(
            {"name": "MS Decimals Product", "type": "consu"})

    def _order(self, company, qty=2.555, price=1.234):
        return self.env["sale.order"].with_company(company).create({
            "company_id": company.id,
            "partner_id": self.partner.id,
            "order_line": [(0, 0, {
                "product_id": self.product.id,
                "product_uom_qty": qty,
                "price_unit": price,
            })],
        })

    def _cells(self, order):
        """The printed QUANTITY and UNIT PRICE cells of the single order line."""
        html = self.env["ir.actions.report"]._render_qweb_html(
            "sale.report_saleorder", [order.id])[0].decode()
        qty = re.search(r'name="td_product_quantity".*?</td>', html, re.S)
        price = re.search(r'name="td_product_priceunit".*?</td>', html, re.S)
        self.assertTrue(qty and price, "the line cells are missing from the report")
        return qty.group(0), price.group(0)

    # --- the Raja companies ---------------------------------------------------

    def test_raja_quantity_prints_two_decimals(self):
        qty, _price = self._cells(self._order(self.raja))
        self.assertIn("2.56", qty)
        self.assertNotIn("2.555", qty)

    def test_raja_unit_price_prints_two_decimals(self):
        _qty, price = self._cells(self._order(self.raja))
        self.assertIn("1.23", price)
        self.assertNotIn("1.234", price)

    def test_raja_rounds_the_print_only(self):
        """The stored values keep their decimals - this is a display change."""
        order = self._order(self.raja)
        self._cells(order)
        self.assertEqual(order.order_line.price_unit, 1.234)
        self.assertEqual(order.order_line.product_uom_qty, 2.555)

    # --- every other company --------------------------------------------------

    def test_another_company_keeps_its_decimals(self):
        qty, price = self._cells(self._order(self.other))
        self.assertIn("2.555", qty, "a non-Raja company must print as before")
        self.assertIn("1.234", price, "a non-Raja company must print as before")

    def test_decimal_accuracy_is_untouched(self):
        """The client asked for the print only - the settings must not move."""
        precision = self.env["decimal.precision"]
        self.assertEqual(precision.precision_get("Product Price"), 3)
        self.assertEqual(precision.precision_get("Product Unit"), 3)
