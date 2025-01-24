# -*- coding: utf-8 -*-

from odoo import fields,models,api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    allow_paid_maternity_leave_days = fields.Float(
        string="Allowed Paid Maternity Leave (Days)",
        config_parameter="custom_hr_settings.allow_paid_maternity_leave_days",
        help="Specify the maximum number of days allowed for Paid Maternity Leave.",
        default=70.0
    )

    allow_unpaid_maternity_leave_days = fields.Float(
        string="Allowed Unpaid Maternity Leave (Days)",
        config_parameter="custom_hr_settings.allow_unpaid_maternity_leave_days",
        help="Specify the maximum number of days allowed for Unpaid Maternity Leave.",
        default=120.0
    )

