# -*- coding: utf-8 -*-

from odoo import fields,models,api

class ResConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    allow_late_coming_minutes = fields.Float(
        string="Allowed Late Coming (Minutes)",
        config_parameter="custom_attendance_deduction.allow_late_coming_minutes",
        help="Specify the number of minutes employees are allowed to check in late without it being marked as late attendance.",
        default=15.0
    )

    total_working_hours = fields.Float(
        string="Total Working Hours",
        config_parameter="custom_attendance_deduction.total_working_hours",
        help="Define the total working hours per day",
        default=8.0
    )

    total_working_days_per_month = fields.Float(
        string="Total Working Days Per Month",
        config_parameter="custom_attendance_deduction.working_days_per_month",
        help="Define the standard number of working days in a month for attendance and payroll calculations.",
        default=26.0
    )
