# -*- coding: utf-8 -*-
from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    # ------------------------------------------------------------------
    # Helpers for the MicroSolutions Kuwait invoice layout
    # ------------------------------------------------------------------
    def _ms_line_text(self, line):
        """Split an invoice line into the bold title / light sub-line the design shows."""
        name = (line.name or "").strip()
        parts = [p.strip() for p in name.splitlines() if p.strip()]
        title = line.product_id.name or "" if line.product_id else ""
        if not title:
            title = parts[0] if parts else ""
            parts = parts[1:]
        elif parts and (parts[0] == title or parts[0].endswith(title)):
            # the line description usually repeats "[CODE] Product name" first
            parts = parts[1:]
        return title, " ".join(parts)

    def _ms_format_qty(self, qty):
        """Whole quantities print bare - the client wants "1", not "1.00".

        Fractions keep the digits they need, so 2.5 still prints as 2.5.
        """
        # Read the precision off the field itself: the decimal.precision
        # application was renamed "Product Unit of Measure" -> "Product Unit"
        # in v19, and a stale name silently falls back to 2 digits.
        digits = self.env["account.move.line"]._fields["quantity"].get_digits(self.env)
        precision = digits[1] if digits else 2
        text = "{0:,.{1}f}".format(qty, precision)
        if "." in text:
            text = text.rstrip("0").rstrip(".")
        return text or "0"

    def _ms_report_lines(self):
        """Printable lines, in order, numbered from 1."""
        self.ensure_one()
        res = []
        lines = self.invoice_line_ids.filtered(lambda l: l.display_type == "product")
        for index, line in enumerate(lines, start=1):
            title, desc = self._ms_line_text(line)
            res.append({
                "seq": index,
                "title": title,
                "desc": desc,
                "qty": self._ms_format_qty(line.quantity),
                "price": line.price_unit,
                "amount": line.price_subtotal,
            })
        return res

    def _ms_report_totals(self):
        """Subtotal is shown gross, with the line discounts pulled out on their own row."""
        self.ensure_one()
        lines = self.invoice_line_ids.filtered(lambda l: l.display_type == "product")
        gross = sum(line.quantity * line.price_unit for line in lines)
        return {
            "gross": gross,
            "discount": gross - self.amount_untaxed,
            "tax": self.amount_tax,
            "total": self.amount_total,
            "due": self.amount_residual,
        }

    def _ms_amount_in_words(self):
        self.ensure_one()
        return self.currency_id.amount_to_text(self.amount_total)

    def _ms_partner_lines(self):
        """The BILL TO block: address / phone / email / VAT, blanks dropped."""
        self.ensure_one()
        partner = self.partner_id
        street = ", ".join(p for p in (partner.street, partner.street2) if p)
        city = ", ".join(p for p in (
            partner.city,
            partner.state_id.name,
            partner.country_id.name,
        ) if p)
        res = []
        if street:
            res.append(street)
        if city:
            res.append(city)
        if partner.phone:
            res.append("Phone: %s" % partner.phone)
        if partner.email:
            res.append("Email: %s" % partner.email)
        if partner.vat:
            res.append("VAT No. %s" % partner.vat)
        return res
