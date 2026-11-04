# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestMsInvoiceReport(TransactionCase):
    """Amount in words and section rows on the MicroSolutions invoice."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.kwd = cls.env["res.currency"].with_context(active_test=False).search(
            [("name", "=", "KWD")], limit=1)
        cls.kwd.active = True
        cls.usd = cls.env["res.currency"].with_context(active_test=False).search(
            [("name", "=", "USD")], limit=1)
        cls.usd.active = True
        cls.partner = cls.env["res.partner"].create({"name": "MS Invoice Customer"})

    def _invoice(self, currency, price, sections=()):
        lines = [(0, 0, {"display_type": "line_section", "name": name}) for name in sections]
        lines.append((0, 0, {"name": "MS Line", "quantity": 1, "price_unit": price, "tax_ids": False}))
        return self.env["account.move"].create({
            "move_type": "out_invoice",
            "partner_id": self.partner.id,
            "currency_id": currency.id,
            "invoice_line_ids": lines,
        })

    # --- amount in words ------------------------------------------------------

    def test_kwd_reads_kuwaiti_dinars_without_commas(self):
        self.assertEqual(
            self._invoice(self.kwd, 1375)._ms_amount_in_words(),
            "One Thousand Three Hundred And Seventy-Five Kuwaiti Dinars")

    def test_kwd_keeps_the_fils(self):
        self.assertEqual(
            self._invoice(self.kwd, 60.5)._ms_amount_in_words(),
            "Sixty Kuwaiti Dinars and Five Hundred Fils")

    def test_one_dinar_is_singular(self):
        self.assertEqual(self._invoice(self.kwd, 1)._ms_amount_in_words(), "One Kuwaiti Dinar")

    def test_another_currency_keeps_its_own_label(self):
        text = self._invoice(self.usd, 1375)._ms_amount_in_words()
        self.assertNotIn(",", text)
        self.assertNotIn("Kuwaiti", text)
        self.assertIn(self.usd.currency_unit_label, text)

    def test_the_currency_label_is_untouched(self):
        self._invoice(self.kwd, 1375)._ms_amount_in_words()
        self.assertEqual(self.kwd.with_context(lang="en_US").currency_unit_label, "Dinar")

    # --- section rows ---------------------------------------------------------

    def test_sections_print_and_do_not_take_a_number(self):
        rows = self._invoice(self.kwd, 100, sections=["MS Section"])._ms_report_lines()
        self.assertEqual([row["kind"] for row in rows], ["section", "product"])
        self.assertEqual(rows[0]["title"], "MS Section")
        self.assertEqual(rows[1]["seq"], 1)

    def test_rows_follow_the_order_on_the_invoice(self):
        """A section added after its product but dragged above it prints above it."""
        invoice = self._invoice(self.kwd, 100)
        product = invoice.invoice_line_ids
        product.sequence = 5
        self.env["account.move.line"].create({
            "move_id": invoice.id,
            "display_type": "line_section",
            "name": "MS Section",
            "sequence": 1,
        })
        invoice.invalidate_recordset(["invoice_line_ids"])
        rows = invoice._ms_report_lines()
        self.assertEqual([row["kind"] for row in rows], ["section", "product"])

    def test_note_prints_where_it_was_typed_without_a_number(self):
        invoice = self._invoice(self.kwd, 100)
        invoice.invoice_line_ids.sequence = 1
        self.env["account.move.line"].create({
            "move_id": invoice.id,
            "display_type": "line_note",
            "name": "MS Note",
            "sequence": 2,
        })
        invoice.invalidate_recordset(["invoice_line_ids"])
        rows = invoice._ms_report_lines()
        self.assertEqual([row["kind"] for row in rows], ["product", "note"])
        self.assertEqual(rows[1]["title"], "MS Note")
        self.assertEqual(rows[0]["seq"], 1)
        html = self.env["ir.actions.report"]._render_qweb_html(
            "ms_invoice_report.report_ms_invoice", invoice.ids)[0].decode()
        self.assertIn("MS Note", html)
        self.assertIn('class="ms-note"', html)

    def test_section_prints_on_the_pdf_html(self):
        invoice = self._invoice(self.kwd, 100, sections=["MS Section"])
        html = self.env["ir.actions.report"]._render_qweb_html(
            "ms_invoice_report.report_ms_invoice", invoice.ids)[0].decode()
        self.assertIn("MS Section", html)
        self.assertIn('class="ms-sec"', html)
