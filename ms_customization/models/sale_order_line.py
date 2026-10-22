# -*- coding: utf-8 -*-
from odoo import api, fields, models


class SaleOrderLine(models.Model):
    _inherit = "sale.order.line"

    ms_part_number = fields.Char(
        string="Part Number",
        help="The customer's or supplier's own part number for this line. Shown "
             "and printed only for Safety Plus World.",
    )

    ms_is_spw_company = fields.Boolean(
        related="order_id.ms_is_spw_company",
        string="Is Safety Plus World",
    )
