# -*- coding: utf-8 -*-
from odoo import fields, models


class CrmStage(models.Model):
    _inherit = "crm.stage"

    is_quotation_stage = fields.Boolean(
        string="Is Quotation Stage?",
        help="Opportunities move to this stage automatically when a quotation is "
             "created for them. Set it on one stage per sales team; a stage shared "
             "with all teams acts as the fallback.",
    )
