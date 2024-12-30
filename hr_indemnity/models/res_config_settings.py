# -*- coding: utf-8 -*-
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    allow_employee_indemnity = fields.Boolean(
        string="Allow Indemnity",
        config_parameter="hr_indemnity.allow_employee_indemnity",
    )
    indemnity_start_year = fields.Char(
        string="Allow Indemnity From Year",
        config_parameter="hr_indemnity.indemnity_start_year",
    )
