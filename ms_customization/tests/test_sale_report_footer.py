# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged

RAJA_NAME = "RAJA INTERNATIONAL GENERAL TRADING (LLC)"
OLD_FOOTER = "<p>+971581263151 info@rajacompany.com https://rajacompany.com 999888777</p>"


@tagged("post_install", "-at_install")
class TestSaleReportFooter(TransactionCase):
    """The quotation footer is overridden for the Raja companies only."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Company = cls.env["res.company"]
        boxed = cls.env.ref("web.external_layout_boxed")

        cls.raja = Company.search([("name", "=", RAJA_NAME)], limit=1) \
            or Company.create({"name": RAJA_NAME})
        cls.other = Company.create({"name": "MS Footer Not Raja"})
        cls.env.user.company_ids = [(4, cls.raja.id), (4, cls.other.id)]
        for company in (cls.raja, cls.other):
            company.write({
                "report_footer": OLD_FOOTER,
                "vat": "TRN:123456789000003",
                "external_report_layout_id": boxed.id,
            })

        cls.partner = cls.env["res.partner"].create({"name": "MS Footer Customer"})

    def _order(self, company):
        return self.env["sale.order"].with_company(company).create({
            "company_id": company.id,
            "partner_id": self.partner.id,
        })

    def _html(self, record, report):
        return self.env["ir.actions.report"]._render_qweb_html(
            report, [record.id])[0].decode()

    def test_raja_quotation_shows_the_new_footer(self):
        html = self._html(self._order(self.raja), "sale.report_saleorder")
        self.assertIn("+971582563078", html)
        self.assertIn("sc1@rajacompany.com", html)
        self.assertIn("safetyplusworld.com", html)

    def test_raja_quotation_drops_the_old_values(self):
        html = self._html(self._order(self.raja), "sale.report_saleorder")
        self.assertNotIn("+971581263151", html)
        self.assertNotIn("info@rajacompany.com", html)
        self.assertNotIn("https://rajacompany.com", html)

    def test_the_trn_is_left_alone(self):
        """Only the three values are replaced; the TRN stays as it was."""
        html = self._html(self._order(self.raja), "sale.report_saleorder")
        self.assertIn("TRN:123456789000003", html)

    def test_the_website_is_a_clickable_link(self):
        """Shown with the https:// prefix and rendered as a link, as before."""
        html = self._html(self._order(self.raja), "sale.report_saleorder")
        self.assertIn('<a href="https://safetyplusworld.com">https://safetyplusworld.com</a>', html)

    def test_another_company_keeps_its_own_footer(self):
        html = self._html(self._order(self.other), "sale.report_saleorder")
        self.assertIn("+971581263151", html)
        self.assertNotIn("safetyplusworld.com", html)

    def test_other_documents_are_untouched(self):
        """A Raja invoice must still print the company's real footer."""
        invoice = self.env["account.move"].with_company(self.raja).create({
            "move_type": "out_invoice",
            "company_id": self.raja.id,
            "partner_id": self.partner.id,
        })
        html = self._html(invoice, "account.report_invoice")
        self.assertIn("+971581263151", html)
        self.assertNotIn("safetyplusworld.com", html,
                         "the override must not leak outside the sale order report")
