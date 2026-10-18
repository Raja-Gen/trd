# -*- coding: utf-8 -*-
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    is_ibuysafety_company = fields.Boolean(
        string="iBuySafety Website Features",
        help="Enables the customer website pricelists and the product document "
             "link for this company and its website.",
    )
