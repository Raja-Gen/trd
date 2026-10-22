# -*- coding: utf-8 -*-
from lxml import etree

from odoo.tests.common import TransactionCase, tagged

SPW_NAME = "SAFETY PLUS WORLD (UK) LIMITED"


@tagged("post_install", "-at_install")
class TestSalePartNumber(TransactionCase):
    """Part Number on the order lines, for Safety Plus World only."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Company = cls.env["res.company"]
        cls.spw = Company.search([("name", "=", SPW_NAME)], limit=1) \
            or Company.create({"name": SPW_NAME})
        cls.other = Company.create({"name": "MS Part No Not SPW"})
        cls.env.user.company_ids = [(4, cls.spw.id), (4, cls.other.id)]

        cls.partner = cls.env["res.partner"].create({"name": "MS Part No Customer"})
        cls.product = cls.env["product.product"].create(
            {"name": "MS Part No Product", "type": "consu"})

    def _order(self, company, part_number=False):
        return self.env["sale.order"].with_company(company).create({
            "company_id": company.id,
            "partner_id": self.partner.id,
            "order_line": [(0, 0, {
                "product_id": self.product.id,
                "product_uom_qty": 1,
                "price_unit": 10,
                "ms_part_number": part_number,
            })],
        })

    def _html(self, order):
        return self.env["ir.actions.report"]._render_qweb_html(
            "sale.report_saleorder", [order.id])[0].decode()

    # --- the field ------------------------------------------------------------

    def test_field_is_an_optional_char(self):
        field = self.env["sale.order.line"]._fields["ms_part_number"]
        self.assertEqual(field.type, "char")
        self.assertFalse(field.required, "Part Number must stay optional")

    def test_it_holds_what_was_typed(self):
        order = self._order(self.spw, "FMEVEST4XOR")
        self.assertEqual(order.order_line.ms_part_number, "FMEVEST4XOR")

    def test_the_company_flag_reads_the_orders_own_company(self):
        self.assertTrue(self._order(self.spw).ms_is_spw_company)
        self.assertFalse(self._order(self.other).ms_is_spw_company)
        # and the line can see it, which is what the PDF condition uses
        self.assertTrue(self._order(self.spw).order_line.ms_is_spw_company)

    # --- the order form -------------------------------------------------------

    def test_the_column_is_on_the_form_and_hidden_for_others(self):
        arch = etree.fromstring(
            self.env["sale.order"].get_view(self.env.ref("sale.view_order_form").id)["arch"])
        column = arch.xpath("//field[@name='order_line']/list/field[@name='ms_part_number']")
        self.assertTrue(column, "Part Number is missing from the order lines")
        self.assertIn("not parent.ms_is_spw_company", column[0].get("column_invisible"))

    # --- the quotation PDF ----------------------------------------------------

    def test_report_prints_the_column_for_spw(self):
        order = self._order(self.spw, "FMEVEST4XOR")
        html = self._html(order)
        self.assertIn("Part No.", html)
        self.assertIn("FMEVEST4XOR", html)

    def test_report_omits_the_column_when_no_line_has_one(self):
        """An order with no part numbers keeps the layout it has today."""
        self.assertNotIn("Part No.", self._html(self._order(self.spw)))

    def test_report_omits_the_column_for_another_company(self):
        order = self._order(self.other, "FMEVEST4XOR")
        html = self._html(order)
        self.assertNotIn("Part No.", html)
        self.assertNotIn("FMEVEST4XOR", html)

    def test_report_header_and_body_cells_stay_aligned(self):
        """A column that prints one more <th> than <td> shifts every figure."""
        order = self._order(self.spw, "FMEVEST4XOR")
        doc = etree.fromstring(self._html(order), etree.HTMLParser())
        table = doc.xpath("//table[contains(@class, 'o_main_table')]")[0]
        header = table.xpath(".//thead/tr/th")
        cells = table.xpath(".//tr[@name='tr_product']")[0].xpath("./td")
        span = sum(int(th.get("colspan", 1)) for th in header)
        self.assertEqual(span, len(cells),
                         "header columns and line cells must add up")
