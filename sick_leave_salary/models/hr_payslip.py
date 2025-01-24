# -*- coding: utf-8 -*-

import datetime
from odoo import fields, models, api


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    def _get_payslip_lines(self):
        line_vals = super()._get_payslip_lines()
        filtered_line_vals = [
            item
            for item in line_vals
            if isinstance(item, dict) and "rate" in item and item["rate"] != 0.0
        ]
        return filtered_line_vals
