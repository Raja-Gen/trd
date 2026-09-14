# -*- coding: utf-8 -*-
from lxml import etree

from odoo.tests.common import TransactionCase, tagged

RAJA_NAME = "RAJA INTERNATIONAL GENERAL TRADING (LLC)"


@tagged("post_install", "-at_install")
class TestAttnTo(TransactionCase):
    """Attn To on the sale order, shown only for the Raja group companies."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Company = cls.env["res.company"]
        cls.raja = Company.search([("name", "=", RAJA_NAME)], limit=1) \
            or Company.create({"name": RAJA_NAME})
        cls.other = Company.create({"name": "MS Attn Not Raja"})
        cls.env.user.company_ids = [(4, cls.raja.id), (4, cls.other.id)]

        cls.partner = cls.env["res.partner"].create({"name": "MS Attn Customer"})
        cls.contact = cls.env["res.partner"].create(
            {"name": "MS Attn Contact", "parent_id": cls.partner.id})

    def _order(self, company):
        return self.env["sale.order"].with_company(company).create({
            "company_id": company.id,
            "partner_id": self.partner.id,
        })

    # --- the field ------------------------------------------------------------

    def test_field_is_a_contact_link(self):
        field = self.env["sale.order"]._fields["ms_attn_to_id"]
        self.assertEqual(field.type, "many2one")
        self.assertEqual(field.comodel_name, "res.partner")
        self.assertFalse(field.required, "Attn To must stay optional")

    def test_it_holds_a_contact(self):
        order = self._order(self.raja)
        order.ms_attn_to_id = self.contact
        self.assertEqual(order.ms_attn_to_id, self.contact)

    # --- company scoping ------------------------------------------------------

    def test_flag_is_true_only_for_a_raja_company(self):
        self.assertTrue(self._order(self.raja).ms_is_raja_company)
        self.assertFalse(self._order(self.other).ms_is_raja_company)

    def test_flag_follows_the_order_not_the_active_company(self):
        """Opening a Raja order from another company must still show the field."""
        order = self._order(self.raja).with_context(
            allowed_company_ids=[self.other.id, self.raja.id])
        self.assertTrue(order.ms_is_raja_company)

    def test_flag_reacts_to_changing_the_company(self):
        order = self._order(self.other)
        self.assertFalse(order.ms_is_raja_company)
        order.company_id = self.raja
        order.invalidate_recordset(["ms_is_raja_company"])
        self.assertTrue(order.ms_is_raja_company)

    # --- the form -------------------------------------------------------------

    def test_field_sits_directly_under_revision(self):
        view = self.env.ref("sale.view_order_form")
        arch = etree.fromstring(
            self.env["sale.order"].get_view(view_id=view.id, view_type="form")["arch"])

        attn = arch.xpath("//field[@name='ms_attn_to_id']")
        self.assertTrue(attn, "Attn To is missing from the sale order form")
        self.assertIn("not ms_is_raja_company", attn[0].get("invisible"),
                      "Attn To must be hidden for non-Raja companies")

        revision = arch.xpath("//field[@name='order_revise']")
        self.assertTrue(revision, "the Revision field is not on the form")
        siblings = list(revision[0].getparent())
        self.assertLess(siblings.index(revision[0]), siblings.index(attn[0]),
                        "Attn To must come after Revision")

    # --- the quotation PDF ----------------------------------------------------

    def _html(self, order):
        return self.env["ir.actions.report"]._render_qweb_html(
            "sale.report_saleorder", [order.id])[0].decode()

    def test_report_prints_attn_to_for_a_raja_company(self):
        order = self._order(self.raja)
        order.ms_attn_to_id = self.contact
        html = self._html(order)
        self.assertIn("Attn To:", html)
        self.assertIn(self.contact.name, html)

    def test_report_omits_attn_to_when_empty(self):
        """Nothing is printed when the field has no value."""
        order = self._order(self.raja)
        self.assertFalse(order.ms_attn_to_id)
        self.assertNotIn("Attn To:", self._html(order))

    def test_report_omits_attn_to_for_another_company(self):
        order = self._order(self.other)
        order.ms_attn_to_id = self.contact
        self.assertNotIn("Attn To:", self._html(order),
                         "Attn To must not reach a non-Raja company's report")

    def test_report_still_prints_the_customer_trn(self):
        """TRN is Odoo's own line - adding Attn To must not disturb it."""
        self.partner.vat = "100236860100003"
        order = self._order(self.raja)
        html = self._html(order)
        self.assertIn("100236860100003", html)

    def test_report_omits_trn_when_the_customer_has_none(self):
        self.partner.vat = False
        order = self._order(self.raja)
        self.assertNotIn("100236860100003", self._html(order))

    # --- unit price shown with 2 decimals (display only) ----------------------

    def test_the_module_does_not_redefine_price_unit(self):
        """Deliberate: this fix is display-only.

        Re-attaching digits='Product Price' to the field would fix the display
        too, but it rounds every stored unit price when the column converts -
        181 live lines on production carry a 3rd decimal. If someone adds that
        override later, this test is the reminder of why it was avoided.
        """
        field = self.env["ir.model.fields"].search([
            ("model", "=", "sale.order.line"), ("name", "=", "price_unit")], limit=1)
        self.assertNotIn("ms_customization", (field.modules or "").split(","),
                         "price_unit must not be redefined by this module")

    def test_form_pins_the_unit_price_column(self):
        view = self.env.ref("sale.view_order_form")
        arch = etree.fromstring(
            self.env["sale.order"].get_view(view_id=view.id, view_type="form")["arch"])
        nodes = arch.xpath("//field[@name='order_line']//field[@name='price_unit']")
        self.assertTrue(nodes, "the order line unit price is missing from the form")
        self.assertEqual(nodes[0].get("digits"), "[16, 2]")

    def test_report_pins_the_unit_price(self):
        """Read the COMBINED arch - the attribute lives in our inheriting view."""
        view = self.env.ref("sale.report_saleorder_document")
        arch = view._get_combined_arch() if hasattr(view, "_get_combined_arch") \
            else etree.fromstring(view.read_combined(["arch"])["arch"])
        node = arch.xpath("//td[@name='td_product_priceunit']/span[@t-field='line.price_unit']")
        self.assertTrue(node, "the printed unit price node moved")
        self.assertIn("'precision': 2", node[0].get("t-options") or "")
