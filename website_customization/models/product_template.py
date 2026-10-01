import math

from odoo import models, fields, api

class ProductTemplate(models.Model):
    _inherit = "product.template"

    freeze_stock = fields.Boolean(
        string="Freeze Stock",
        help="If checked, this product cannot be sold (website add-to-cart disabled and sale order confirmation blocked)."
    )

    website_qty_available = fields.Float(
        string="Website Quantity",
        compute='_compute_website_qty_available'
    )

    def _compute_website_qty_available(self):
        for rec in self:
            rec.website_qty_available = rec.sudo().qty_available

    def _get_additionnal_combination_info(self, product_or_template, quantity, uom, date, website):
        """Expose the *selected variant* on-hand quantity to the product page.

        `qty_available` on a template is the sum of all its variants, so the
        website has to read it from the variant of the current combination
        instead. The value is refreshed on every variant change through
        `/website_sale/get_combination_info`.
        """
        res = super()._get_additionnal_combination_info(
            product_or_template, quantity, uom, date, website
        )
        qty = (
            product_or_template.sudo().qty_available
            if product_or_template.is_product_variant
            else 0.0
        )
        res['freeze_stock'] = product_or_template.freeze_stock
        res['website_variant_qty_available'] = qty
        # Website-only display value: products are sold per piece/pair, so the
        # decimals are always zero and only add noise. Rounded down so we never
        # advertise more than what is on hand.
        res['website_variant_qty_available_str'] = str(int(math.floor(qty)))
        return res

class ProductProduct(models.Model):
    _inherit = "product.product"

    freeze_qty = fields.Float("Frozen Quantity", default=0.0)

    @api.depends('qty_available', 'freeze_qty')
    def _compute_virtual_available(self):
        super(ProductProduct, self)._compute_virtual_available()
        for product in self:
            product.virtual_available -= product.freeze_qty