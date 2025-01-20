# -*- coding: utf-8 -*-

from odoo import fields,models,api
from datetime import datetime, timedelta

class HrPayslipWorkedDays(models.Model):
    _inherit = 'hr.payslip.worked_days'

    unpaid_days = fields.Float(string="Unpaid Leave Days", compute="_compute_unpaid_days", store=True)
    working_days = fields.Float(string="Total Working Days", compute="_compute_working_days", store=True)
    prorated_factor = fields.Float(string="Prorated Factor", compute="_compute_prorated_factor", store=True)

    @api.depends('payslip_id.employee_id', 'payslip_id.date_from', 'payslip_id.date_to')
    def _compute_unpaid_days(self):
        for record in self:
            record.unpaid_days = record._get_unpaid_days(
                record.payslip_id.employee_id,
                self.convert_tzinfo(record.payslip_id.date_from),
                self.convert_tzinfo(record.payslip_id.date_to),
            )

    @api.depends('payslip_id.employee_id', 'payslip_id.date_from', 'payslip_id.date_to')
    def _compute_working_days(self):
        for record in self:
            config_settings = self.env['res.config.settings'].search([], limit=1)
            record.working_days = config_settings.total_working_days_per_month if config_settings else 26

    @api.depends('unpaid_days', 'working_days')
    def _compute_prorated_factor(self):
        for record in self:
            if record.working_days > 0:
                record.prorated_factor = (record.working_days - record.unpaid_days) / record.working_days
            else:
                record.prorated_factor = 0.0

    def _get_unpaid_days(self, employee, date_from, date_to):
        leaves = self.env['hr.leave'].search([
            ('employee_id', '=', employee.id),
            ('date_from', '>=', date_from),
            ('date_to', '<=', date_to),
            ('state', '=', 'validate'),
            ('holiday_status_id.unpaid', '=', True),
        ])
        return sum(leave.number_of_days for leave in leaves)

    def convert_tzinfo(self, date):
        return datetime.combine(date, datetime.min.time())

