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

class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    l10n_ae_tax_report_counterpart_account = fields.Char(
        string="Liabilities Account",
        config_parameter="l10n_ae_tax_report.liabilities_account",
        help="Account used for tax liabilities.",
    )
        
    l10n_ae_tax_report_liabilities_account = fields.Char(
        string="Counterpart Account",
        config_parameter="l10n_ae_tax_report.counterpart_account",
        help="Account used for counterpart entries.",
    )

    l10n_ae_tax_report_counterpart_account = fields.Many2one(
    'account.account',
    string="Tax Report Counterpart Account"
    )

