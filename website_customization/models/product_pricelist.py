# -*- coding: utf-8 -*-
from odoo import models


class ProductPricelist(models.Model):
    _inherit = "product.pricelist"

    def _is_available_on_website(self, website):
        """A customer's own website pricelists are usable by that customer even
        when they are neither selectable nor promo-code pricelists."""
        if super()._is_available_on_website(website):
            return True
        if self.env.context.get('skip_customer_website_pricelists'):
            return False
        return self.id in website._get_customer_website_pricelists().ids
