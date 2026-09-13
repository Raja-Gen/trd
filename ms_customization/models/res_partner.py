# -*- coding: utf-8 -*-
from odoo import fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    ms_customer_type = fields.Selection(
        [
            ("trader", "Trader"),
            ("end_user", "End User"),
        ],
        string="Customer Type",
        tracking=True,
        help="Classifies the customer: a Trader buys to resell, an End User buys "
             "for their own use. Left empty on contacts nobody has classified yet.",
    )
