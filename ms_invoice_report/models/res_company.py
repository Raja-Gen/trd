# -*- coding: utf-8 -*-
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    ms_invoice_brand = fields.Boolean(
        string="MicroSolutions invoice layout",
        help="Print customer invoices of this company with the MicroSolutions "
             "Kuwait branded layout instead of the standard Odoo one.",
    )
