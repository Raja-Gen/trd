# -*- coding: utf-8 -*-
from odoo.http import request

from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleCustomerPricelist(WebsiteSale):

    def _apply_selectable_pricelist(self, pricelist_id):
        """Let a customer switch to one of their own website pricelists.

        Core only accepts `selectable` pricelists or the partner's default one,
        but customer pricelists are usually hidden from everybody else.
        """
        website = request.env['website'].get_current_website()
        customer_pricelists = website._get_customer_website_pricelists()
        if pricelist_id in customer_pricelists.ids and website.is_pricelist_available(pricelist_id):
            self._apply_pricelist(pricelist=customer_pricelists.browse(pricelist_id))
            return True
        return super()._apply_selectable_pricelist(pricelist_id)
