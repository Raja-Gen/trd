# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    website_pricelist_ids = fields.Many2many(
        "product.pricelist",
        "res_partner_website_pricelist_rel",
        "partner_id",
        "pricelist_id",
        string="Website Pricelists",
        help="Pricelists this customer can choose from on the website, on top of the "
             "public ones. Contacts of a company use the company's pricelists.",
    )
    is_ibuysafety_company = fields.Boolean(compute="_compute_is_ibuysafety_company")

    @api.depends_context("company")
    def _compute_is_ibuysafety_company(self):
        self.is_ibuysafety_company = self.env.company.is_ibuysafety_company
