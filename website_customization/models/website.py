# -*- coding: utf-8 -*-
from odoo import fields, models


class Website(models.Model):
    _inherit = "website"

    # Related fields are read as superuser, so visitors whose own companies
    # do not include the website's company can still evaluate the switch.
    is_ibuysafety_company = fields.Boolean(related="company_id.is_ibuysafety_company")

    def _get_customer_website_pricelists(self):
        """Website pricelists assigned to the logged-in customer (sudo)."""
        self.ensure_one()
        if not self.is_ibuysafety_company or self.env.user._is_public():
            return self.env['product.pricelist']
        partner_sudo = self.env.user.partner_id.sudo().commercial_partner_id
        return partner_sudo.website_pricelist_ids.filtered(
            lambda pl: (not pl.company_id or pl.company_id == self.company_id)
            and (not pl.website_id or pl.website_id == self)
        )

    def _get_pl_partner_order(self, *args, **kwargs):
        # The result is cached without the user in its key, so it must not
        # depend on the customer pricelists; they are added in
        # `get_pricelist_available` instead.
        website = self.with_context(skip_customer_website_pricelists=True)
        return super(Website, website)._get_pl_partner_order(*args, **kwargs)

    def get_pricelist_available(self, show_visible=False):
        pricelists = super().get_pricelist_available(show_visible=show_visible)
        if not self.env['res.groups']._is_feature_enabled('product.group_product_pricelist'):
            return pricelists
        country_code = self._get_geoip_country_code()
        customer_pricelists = self._get_customer_website_pricelists().filtered(
            lambda pl: pl._is_available_in_country(country_code)
        )
        if not customer_pricelists:
            return pricelists
        return pricelists.browse((pricelists.sudo() | customer_pricelists).sorted().ids)
