# -*- coding: utf-8 -*-

from odoo import models, fields
from datetime import datetime, time, timedelta
from odoo.tools.safe_eval import safe_eval


class Payslip(models.Model):
    _inherit = 'hr.payslip'

    is_eos = fields.Boolean('Is EOS', default=False)
    expense_count = fields.Integer("# EOS Benefits", compute='_compute_expense_count')

    def _get_base_local_dict(self):
        res = super()._get_base_local_dict()
        res.update({
            'compute_sick_leave': compute_sick_leave,
            'compute_sick_leave_deduction': compute_sick_leave_deduction,
        })
        return res

    def _compute_expense_count(self):
        """count_data = self.env['hr.expense.sheet'].sudo()._read_group(
            [('employee_id', 'in', self.employee_id.ids), ('state', '=', 'post'), ('date_end', '>=', self.date_from), ('date_end', '<=', self.date_to)],
            ['employee_id'],
            ['employee_id'])
        mapped_counts = {data['employee_id'][0]: data['employee_id_count'] for data in count_data}"""
        for payslip in self:
            count_data = payslip.env['hr.expense.sheet'].sudo().search_count(
            [('employee_id', 'in', payslip.employee_id.ids), ('state', '=', 'post'), ('date_end', '>=', payslip.date_from), ('date_end', '<=', payslip.date_to)])
            payslip.expense_count = count_data

    def action_open_expense(self):
        # open-eos
        self.ensure_one()
        action = self.env["ir.actions.actions"]._for_xml_id("hr_expense.action_hr_expense_account")
        action.update({'domain': [('employee_id', 'in', self.employee_id.ids), ('state', '=', 'post'), ('date_end', '>=', self.date_from), ('date_end', '<=', self.date_to)]})
        return action


def compute_sick_leave(payslip, contract):
    return 0

def compute_lad_deduction(payslip, contract):
    worked_days = 0
    leave_days = 0
    lad = 0
    if payslip.worked_days_line_ids:
        # basic = payslip.worked_days_line_ids.filtered(lambda r: r.code == 'BASIC')
        # fetch_worked_days = payslip.worked_days_line_ids.filtered(lambda r: r.code == 'WORK100')

        # Get the total number of absent days for an employee

        employee_id = contract.employee_id.id  # Replace with the correct employee ID
        start_date = payslip.date_from  # Replace with the correct start date of the period
        end_date = payslip.date_to  # Replace with the correct end date of the period

        # Fetch all approved leave records for the employee within the payslip period
        leave_records = payslip.env['hr.leave'].search([
            ('employee_id', '=', employee_id),
            ('state', '=', 'validate'),  # Only consider validated leaves
            ('request_date_from', '>=', start_date),
            ('request_date_to', '<=', end_date),
            ('holiday_status_id.time_type', '=', 'leave')  # Only consider leave type records
        ])

        basic_salary_rule = payslip.env['hr.salary.rule'].search([
            ('code', '=', 'BASIC'),
            ('struct_id', '=', payslip.env.ref('kuwait_payroll.kuwait_employee_payroll_structure').id),
        ], limit=1)

        # Calculate the total number of days absent
        total_absent_days = sum(leave.number_of_days for leave in leave_records)

        # Initialize the total basic salary
        total_basic_salary = 0.0

        # Iterate through the payslip lines to calculate the total basic salary
        # if basic_records:
        #     total_basic_salary = (contract.wage * basic_records.amount_percentage) / 100

        # Compute the basic salary based on the rule
        # This assumes you have a method or logic to compute the salary based on the rule
        localdict = {
            'contract': contract,
            'employee': payslip.employee_id,
            'categories': {},
            'rules': {},
            'payslip': {},  # Placeholder for payslip context if needed
            'worked_days': [],
            'inputs': [],
        }
        basic_salary = 0.00
        if basic_salary_rule.amount_select == 'fix':
            try:
                basic_salary = basic_salary_rule.amount_fix or 0.0, float(
                    safe_eval(basic_salary_rule.quantity, localdict)), 100.0
            except Exception as e:
                pass
        elif basic_salary_rule.amount_select == 'percentage':
            try:
                basics = (float(safe_eval(basic_salary_rule.amount_percentage_base, localdict)),
                          float(safe_eval(basic_salary_rule.quantity, localdict)),
                          basic_salary_rule.amount_percentage or 0.0)

                # total_basic_salary = (contract.wage * basic_records.amount_percentage) / 100
                total_basic_salary = ((basics[0] * basics[1]) * (basics[2])) / 100
                basic_salary = total_basic_salary
            except Exception as e:
                pass
        else:  # python code
            try:
                safe_eval(basic_salary_rule.amount_python_compute or 0.0, localdict, mode='exec', nocopy=True)
                basics = float(localdict['result']), localdict.get('result_qty', 1.0), localdict.get(
                    'result_rate', 100.0)
                basic_salary = basics[0]
            except Exception as e:
                pass

        # if fetch_worked_days:
        #     worked_days = fetch_worked_days.number_of_days

        if total_absent_days:
            leave_days = total_absent_days
        # total_working_days = worked_days + leave_days
        total_working_days = contract.basic_number_of_days
        if basic_salary > 0.00 and leave_days > 0 and total_working_days > 0:
            days = leave_days/total_working_days #4/26 == 0.1538
            lad = days * basic_salary
            lad = -abs(lad)
    return lad


def compute_sick_leave_deduction(payslip, contract, is_lad=False):
    if is_lad:
        return compute_lad_deduction(payslip, contract)
    else:
        # leave_days = payslip.worked_days_line_ids.filtered(lambda r: r.code == '75_SICK_LEAVE_DEDUCTION').number_of_days
        # domain = [('time_type', '=', 'leave')]
        # Convert date_from and date_to to datetime objects if they are not already
        payslip_date_from = payslip.date_from
        payslip_date_to = payslip.date_to
        # date_from = contract.date_start
        # date_to = contract.date_end
        if not isinstance(payslip.date_from, datetime):
            payslip_date_from = datetime.combine(payslip.date_from, time.min)
        if not isinstance(payslip.date_to, datetime):
            payslip_date_to = datetime.combine(payslip.date_to, time.max)
        # Get the current year
        current_year = datetime.now().year
        previous_date_to = payslip_date_from - timedelta(days=1)

        # Create datetime objects for January 1st and December 31st of the current year
        date_from = datetime(current_year, 1, 1, 0, 0, 0)
        date_to = datetime(current_year, 12, 31, 23, 59, 59, 999999)
        # get_current_leave_days = contract.employee_id._get_leave_days_data_batch(payslip_date_from, payslip_date_to, domain=domain)
        total_payslips = payslip.env['hr.payslip'].search([
            ('contract_id', '=', contract.id),
            ('employee_id', '=', contract.employee_id.id),
            ('date_from', '>=', date_from),
            ('date_to', '<=', date_to)
        ])
        previous_payslips = payslip.env['hr.payslip'].search([
            ('contract_id', '=', contract.id),
            ('employee_id', '=', contract.employee_id.id),
            ('date_from', '>=', date_from),
            ('date_to', '<=', previous_date_to)
        ])
        # get_total_leave_days = contract.employee_id._get_leave_days_data_batch(date_from, date_to, domain=domain)
        # get_previous_leave_days = contract.employee_id._get_leave_days_data_batch(date_from, previous_date_to, domain=domain)
        total_leave_days = 0
        # Iterate through each payslip
        for payslip in total_payslips:
            # Filter worked days to include only leaves of type 'LEAVE110'
            leave_days = payslip.worked_days_line_ids.filtered(lambda r: r.code == 'LEAVE110')

            # Sum up the number of leave days for each payslip
            total_leave_days += sum(leave_days.mapped('number_of_days'))
        previous_leave_days = 0
        for previous_payslip in previous_payslips:
            # Filter worked days to include only leaves of type 'LEAVE110'
            leave_days = previous_payslip.worked_days_line_ids.filtered(lambda r: r.code == 'LEAVE110')

            # Sum up the number of leave days for each payslip
            previous_leave_days += sum(leave_days.mapped('number_of_days'))

        worked_days = 0
        leave_days = 0
        fetch_worked_days = payslip.worked_days_line_ids.filtered(lambda r: r.code == 'WORK100')
        fetch_leave_days = payslip.worked_days_line_ids.filtered(lambda r: r.code == 'LEAVE110')
        if fetch_worked_days:
            worked_days = fetch_worked_days.number_of_days

        if fetch_leave_days:
            leave_days = fetch_leave_days.number_of_days
        # if get_current_leave_days:
        #     leave_days = get_current_leave_days[contract.employee_id.id]['days']
        # if get_total_leave_days:
        #     total_leave_days = get_total_leave_days[contract.employee_id.id]['days']

        # if get_previous_leave_days:
        #     previous_leave_days = get_previous_leave_days[contract.employee_id.id]['days']
        total_working_days = worked_days + leave_days
        deduction = 0
        # sick_leave_wage = 0

        if contract.wage > 0 and total_working_days > 0 and leave_days > 0 and total_leave_days > 15:
            per_day_wage = contract.wage / total_working_days  # 500/22
            wage = contract.wage
            #calculate actual leaves without first 15-days
            l_days = 0
            payout = 0
            if previous_leave_days > 15:
                l_days = leave_days
                payout = per_day_wage * worked_days  # 241.8
            else:
                l_days = leave_days - 15
                payout = per_day_wage * 15  # 241.8

            if total_leave_days <= 25:
                #Half salary (100rs salary than 50rs)
                deduction = per_day_wage * 0.5 # 8.6
                # deduction = wage - deduction
                deduction = deduction * l_days #8.6 * 10 == 86
                deduction = (deduction + payout) - wage #[(86+214.8) - 500)] = -172.2

                # sick_leave_wage = (10 * wage) + ((leave_days - 10) * (wage * 0.5))
            elif total_leave_days <= 35:
                #(100rs salary than 25rs)
                deduction = per_day_wage * 0.25
                # deduction = wage - deduction
                deduction = deduction * l_days
                deduction = (deduction + payout) - wage
                # sick_leave_wage = (10 * wage) + (15 * (wage * 0.5)) + ((leave_days - 25) * (wage * 0.25))
            elif total_leave_days <= 45:
                #(100rs salary than 12.5rs)
                deduction = per_day_wage * 0.125
                # deduction = wage - deduction
                deduction = deduction * l_days
                deduction = (deduction + payout) - wage
                # sick_leave_wage = (10 * wage) + (15 * (wage * 0.5)) + (10 * (wage * 0.25)) + (
                #             (leave_days - 35) * (wage * 0.125))
            elif total_leave_days <= 75:
                # (100rs salary than 0rs)
                # deduction = per_day_wage * l_days
                # deduction = (deduction + payout) - wage
                deduction = deduction - wage
                # deduction = wage * l_days
                # sick_leave_wage = (10 * wage) + (15 * (wage * 0.5)) + (10 * (wage * 0.25)) + (10 * (wage * 0.125))

        # return sick_leave_wage
        return deduction
