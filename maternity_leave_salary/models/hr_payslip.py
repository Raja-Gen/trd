# -*- coding: utf-8 -*-

from odoo import fields,models,api

class HrPayslip(models.Model):
    _inherit = 'hr.payslip'

    def _get_maternity_leave_days(self, payslip, leave_type):
        """
        Calculate maternity leave days based on type (paid or unpaid).
        """
        self.ensure_one()
        if leave_type == "paid":
            leave_type = self.env['hr.leave.type'].search([('is_paid_maternity', '=', True)], limit=1)
        else:
            leave_type = self.env['hr.leave.type'].search([('is_unpaid_maternity', '=', True)], limit=1)
        if not leave_type:
            return 0
        # Fetch leave days within the payslip period
        # Fetch leaves within the payslip period for the employee
        leaves = self.env['hr.leave'].search([
            ('employee_id', '=', payslip.employee_id.id),
            ('holiday_status_id', '=', leave_type.id),
            ('request_date_to', '>=', payslip.date_from),  # Leave ends after payslip starts
            ('request_date_from', '<=', payslip.date_to)
        ])
        if not leaves:
            return
        total_leave_days = 0
        for leave in leaves:
            # Calculate the overlap days between leave and payslip period
            overlap_start = max(leave.request_date_from, payslip.date_from)
            overlap_end = min(leave.request_date_to, payslip.date_to)

            # Compute days within this overlap
            days_in_overlap = (overlap_end - overlap_start).days + 1  # Include both endpoints
            total_leave_days += days_in_overlap
        config_settings = self.env['res.config.settings'].search([], limit=1)
        total_working_days_per_month = config_settings.total_working_days_per_month if config_settings else 26
        total_leave_days = min(total_working_days_per_month, total_leave_days)
        return (payslip.contract_id.wage / total_working_days_per_month) * (total_leave_days or 1)
