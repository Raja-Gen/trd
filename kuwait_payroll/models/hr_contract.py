#coding: utf-8
from odoo import models, fields, api, _
from datetime import datetime, timedelta, time
from odoo.exceptions import UserError, ValidationError


class HRContract(models.Model):
    _inherit = "hr.contract"

    eos_count = fields.Integer("# EOS Benefits", compute='_compute_eos_count')
    over_time_coef = fields.Float(string="OverTime Coef",help="This field used to get overworking time cost/hour, cost_OVT = OverTime Coef * hour_cost",default=1.0)
    departure_reason_id = fields.Many2one("hr.departure.reason",related="employee_id.departure_reason_id")
    housing_allowance = fields.Monetary(string="Housing Allowance")
    transportation_allowance = fields.Monetary(string="Transportation Allowance")
    other_allowances = fields.Monetary(string="Other Allowances")
    basic_number_of_days = fields.Integer(string="Number of Days", help="Number of days of basic salary.",default=26)
    anual_leave_salary = fields.Monetary(string="Annual leave until today",compute="get_an_leave_salary",help="The amount of accrued leaves until today")
    previous_leave = fields.Monetary(string="Previous Leave Import", compute="get_an_leave_salary", readonly=False, store=True, help="The amount of Previous Leave Balance.")
    eos_indiminity = fields.Monetary(string="EOS indiminity until today",compute="end_of_service",help="The amount of End of service indiminity until today.")
    previous_balance = fields.Monetary(string="Previous Balance Import", compute="end_of_service", readonly=False, store=True, help="The amount of Previous Balance.")
    anual_leave_days = fields.Float(string="Annual leave Days",compute="get_an_leave_salary",help="The number of days of accrued leaves until today")
    eos_indiminity_days = fields.Float(string="EOS Days",compute="end_of_service",help="The number of worked days today.")
    leave_taken = fields.Float(string="taken leaves",compute="get_an_leave_salary",help="The amount of accrued leaves until today")

    def _compute_eos_count(self):
        '''count_data = self.env['salary.computation.line']._read_group(
            [('contract_id', 'in', self.ids)],
            ['contract_id'],
            ['contract_id'])
        mapped_counts = {data['contract_id'][0]: data['contract_id_count'] for data in count_data}'''
        for contract in self:
            scl_count = contract.env['salary.computation.line'].search_count(
            [('contract_id', 'in', contract.ids)])
            contract.eos_count = scl_count

    def action_open_eos(self):
        # open-eos
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("kuwait_payroll.action_view_eos_month_form")
        action.update({'domain': [('contract_id', '=', self.id)]})
        return action

    @api.depends('date_start','date_end')
    def get_an_leave_salary(self):
        for rec in self:
            start_date = rec.date_start if rec.date_start else datetime.now().date()
            end_date = rec.date_end if rec.date_end else datetime.now().date()
            today_date = datetime.now().date()
            start = datetime.combine(start_date, datetime.min.time())
            end = datetime.combine(end_date, datetime.min.time())
            day_rate = float(rec.wage / rec.basic_number_of_days)
            difference = (((end_date - start_date).days) / 365) * 30

            out_days, out_hours = 0, 0
            if start < end:
                out_hours = list(rec._get_work_hours(start, end,
                                                     domain=['|', ('work_entry_type_id.code', '=', 'LEAVE105'),
                                                             ('work_entry_type_id.code', '=', 'LEAVE100')]).items())
                out_hours = sum(oh[1] for oh in out_hours if oh and len(oh) > 0)
                out_days += round(out_hours / rec.resource_calendar_id.hours_per_day)

            latest_last_contract = self.search([('date_end', '<=', start_date), ('employee_id', '=', rec.employee_id.id)], limit=1)
            total = 0.00
            if latest_last_contract:
                start_date = latest_last_contract.date_start
                end_date = latest_last_contract.date_end
                if start_date and end_date:
                    total_day_rate = float(latest_last_contract.wage / latest_last_contract.basic_number_of_days)
                    total_difference = (((end_date - start_date).days) / 365) * 30
                    total = (total_day_rate * total_difference)

            rec.anual_leave_days = (end_date - start_date).days
            rec.leave_taken = out_days
            rec.previous_leave = latest_last_contract.previous_leave + total if latest_last_contract else rec.previous_leave
            rec.anual_leave_salary = rec.previous_leave + (day_rate * difference)

    @api.depends('date_start', 'date_end')
    def end_of_service(self):
        for rec in self:
            rec.eos_indiminity_days = 0
            rec.previous_balance = 0.0
            rec.eos_indiminity = 0.0

            '''start_date = rec.date_start if rec.date_start else datetime.now().date()
            end_date = rec.date_end if rec.date_end else datetime.now().date()
            salary_rule_id = self.env.ref('kuwait_payroll.kuwait_end_of_service_provision_salary_rule')
            latest_last_contract = self.search([('date_end', '<=', start_date), ('employee_id', '=', rec.employee_id.id)], limit=1)
            total = 0.00
            if latest_last_contract:
                domain = [('contract_id', '=', latest_last_contract.id),
                          ('salary_rule_id', '=', salary_rule_id.id)]
                grouped_payslips = self.env['hr.payslip.line'].read_group(domain, ['total:sum'], 'contract_id')
                total = sum(slip['total'] for slip in grouped_payslips)

            current_domain = [('contract_id', '=', rec.id),
                              ('salary_rule_id', '=', salary_rule_id.id)]
            current_grouped_payslips = self.env['hr.payslip.line'].read_group(current_domain, ['total:sum'],
                                                                              'contract_id')
            total_eos = sum(current_slip['total'] for current_slip in current_grouped_payslips) if\
                current_grouped_payslips else 0.00

            rec.eos_indiminity_days = (end_date - start_date).days
            rec.previous_balance = latest_last_contract.previous_balance + total if latest_last_contract else rec.previous_balance
            rec.eos_indiminity = rec.previous_balance + total_eos'''
