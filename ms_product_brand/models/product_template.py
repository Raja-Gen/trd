# -*- coding: utf-8 -*-
from odoo import models, fields, api


class ProductTemplate(models.Model):
    _inherit = "product.template"

    brand_id = fields.Many2one(
        "product.brand",
        string="Product Brand",
        index=True,
        tracking=True,
        help="Select the brand for this product.",
    )
