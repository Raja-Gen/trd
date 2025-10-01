from odoo import models, fields

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
