from odoo import models, fields, api, _
from odoo.exceptions import UserError

class EOSBenefitWizard(models.TransientModel):
    _name = 'eos.benefit.wizard'
    _description = 'EOS Benefit Wizard'

    contract_id = fields.Many2one('hr.contract', string="Contract", required=True)
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    date_start = fields.Date(string="Contract Start Date", required=True)
    date_end = fields.Date(string="Contract End Date", required=True)
    previous_balance = fields.Float(string="Previous Balance")
    eos_indemnity = fields.Float(string="EOS Indemnity")
    salary_computation_ids = fields.One2many('salary.computation.line', 'employee_id', string="Salary Computation")

    def compute_eos_benefits(self):
        salary_rule_id = self.env.ref('kuwait_payroll.hr_salary_rule_eos_benefit')
        # latest_contract = self.env['hr.contract'].search(
        #     [('date_end', '>=', self.date_end), ('employee_id', '=', self.employee_id.id)], limit=1)
        latest_contract = self.contract_id
        if not latest_contract:
            raise UserError('No contract found.')

        date_start = fields.Date.from_string(self.date_start)
        date_end = fields.Date.from_string(self.date_end)
        worked_days = (date_end - date_start).days
        worked_years = worked_days / 365.0

        monthly_salary = latest_contract.wage#800  # Replace with actual value if different
        eos = 0

        if worked_years <= 5:
            # Calculation for the first 5 years
            entitled_days = 5 * 12 * 1.25  # 5 years * 12 months * 1.25 days/month
            eos = (entitled_days / latest_contract.basic_number_of_days) * monthly_salary
        else:
            # Calculation for the first 5 years
            entitled_days_first_5_years = 5 * 12 * 1.25
            eos_first_5_years = (entitled_days_first_5_years / latest_contract.basic_number_of_days) * monthly_salary

            # Calculation for the period beyond 5 years
            additional_years = worked_years - 5
            entitled_days_additional = additional_years * 12 * 2.5
            eos_additional = entitled_days_additional * monthly_salary
            # eos_additional = (entitled_days_additional / latest_contract.basic_number_of_days) * monthly_salary

            eos = eos_first_5_years + eos_additional

        # Apply resignation rules
        if 2 / 3 <= worked_years < 5:
            eos *= 2 / 3
        elif worked_years >= 5:
            eos *= 2 / 3

        self.eos_indemnity = eos

        computation_lines = [{
            'name': salary_rule_id.name,
            'category': salary_rule_id.category_id.name,
            'quantity': 1,
            'rate': self.eos_indemnity,
            'amount': self.eos_indemnity,
            'total': self.eos_indemnity,
            'date_start': self.date_start,
            'date_end': self.date_end,
            'eos_indemnity': self.eos_indemnity,
            'contract_id': self.contract_id.id,
            'salary_rule_id': salary_rule_id.id,
        }]

        self.write({
            'salary_computation_ids': [(0, 0, line) for line in computation_lines]
        })

        # Get latest salary-slip of current contract.
        latest_payslip_line = self.env['hr.payslip.line'].sudo().search([
            ('contract_id', '=', latest_contract.id),
            ('date_to', '>=', self.date_end),
            # ('salary_rule_id', '=', salary_rule_id.id),
        ], limit=1)
        if latest_payslip_line and salary_rule_id.id not in latest_payslip_line.slip_id.line_ids.salary_rule_id.ids:
            latest_payslip_line.slip_id.write({'is_eos': True})
            line_vals = []
            line_vals.append({
                'sequence': salary_rule_id.sequence,
                'code': salary_rule_id.code,
                'name': salary_rule_id.name,
                'salary_rule_id': salary_rule_id.id,
                'contract_id': latest_contract.id,
                'employee_id': latest_contract.employee_id.id,
                'rate': self.eos_indemnity,
                'amount': self.eos_indemnity,
                'quantity': 1,
                'slip_id': latest_payslip_line.slip_id.id,
            })
            self.env['hr.payslip.line'].create(line_vals)
        elif latest_payslip_line and salary_rule_id.id in latest_payslip_line.slip_id.line_ids.salary_rule_id.ids:
            latest_payslip_line.slip_id.write({'is_eos': True})
            latest_payslip_line.slip_id.line_ids.filtered(lambda l: salary_rule_id.id in latest_payslip_line.salary_rule_id.ids).write({
                'rate': self.eos_indemnity,
                'amount': self.eos_indemnity,
                'quantity': 1,
            })
        # if latest_payslip_line and salary_rule_id.id in latest_payslip_line.salary_rule_id.ids:
        #     latest_payslip_line.slip_id.write({'is_eos': True})
        #     latest_payslip_line.filtered(lambda l: salary_rule_id.id in latest_payslip_line.salary_rule_id.ids).write({
        #         'rate': self.eos_indemnity,
        #         'amount': self.eos_indemnity,
        #         'quantity': 1,
        #     })

        action = {
            'name': _('EOS Benefit Computation Results'),
            'view_mode': 'tree',
            'res_model': 'salary.computation.line',
            'type': 'ir.actions.act_window',
            'domain': [('employee_id', '=', self.employee_id.id)],
            'help': '<p class="o_view_nocontent_smiling_face">%s</p>' % _('No duplicates found')
        }
        return action

    # def compute_eos_benefits(self):
    #     #there is two calculations happening,
    #     # one is 5 years with EOS_benefit and another one is more than 5 years.
    #     # so logic here is set the EOS_benefit rule to the latest salary_slip
    #     # also maintain the history of that, So history via smart button like `Payslips`
    #     # History will fetch all the filtered records of EOS-benefit in monthly groups (similar to payslips)
    #
    #
    #
    #     # start_date = contract.first_contract_date
    #     # end_date = contract.date_end
    #     # compensation = contract.wage + contract.housing_allowance + contract.transportation_allowance + contract.other_allowances
    #     # day_rate = float(compensation / contract.basic_number_of_days)
    #     # worked_days = (end_date - start_date).days
    #     # worked_years = float(worked_days / 365)
    #     # eos_limit = compensation * 18
    #     # eos = 0
    #     # # before 5 years computation
    #     # if worked_years & lt;=5:
    #     #     eos = worked_years * 15 * day_rate
    #     #
    #     # # After 5 years computing
    #     # if worked_years > 5:
    #     #     ra = worked_years - 5
    #     #     eos = (75 * day_rate) + (compensation * ra)
    #     #
    #     # # EOS departure computing cases ( 3/12= 0.25  => 3 month test of contract )
    #     # if 0.25 & lt; worked_years & lt; 3:
    #     #     result = 0 if employee.departure_reason_id != contract.env.ref('hr.departure_fired') else eos
    #     # elif 3 & lt;= worked_years & lt;= 5:
    #     #     result = eos * 1 / 2 if employee.departure_reason_id != contract.env.ref('hr.departure_fired') else eos
    #     # elif 5 & lt; worked_years & lt; 10:
    #     #     result = eos * 2 / 3 if employee.departure_reason_id != contract.env.ref('hr.departure_fired') else eos
    #     # else:
    #     #     # case if he worked more than 10 years, he has full end of service with limit of 18 months
    #     #     result = eos if eos & lt;
    #     #     eos_limit else eos_limit
    #     # result = payslip.dict.company_id.currency_id.round(result)
    #
    #
    #     salary_rule_id = self.env.ref('kuwait_payroll.kuwait_end_of_service_provision_salary_rule')
    #     latest_last_contract = self.env['hr.contract'].search([('date_end', '<=', self.date_start), ('employee_id', '=', self.employee_id.id)], limit=1)
    #     total = 0.00
    #     if latest_last_contract:
    #         domain = [('contract_id', '=', latest_last_contract.id), ('salary_rule_id', '=', salary_rule_id.id)]
    #         grouped_payslips = self.env['hr.payslip.line'].read_group(domain, ['total:sum'], 'contract_id')
    #         total = sum(slip['total'] for slip in grouped_payslips)
    #
    #     current_domain = [('employee_id', '=', self.employee_id.id), ('salary_rule_id', '=', salary_rule_id.id)]
    #     current_grouped_payslips = self.env['hr.payslip.line'].read_group(current_domain, ['total:sum'], 'contract_id')
    #     total_eos = sum(current_slip['total'] for current_slip in current_grouped_payslips) if current_grouped_payslips else 0.00
    #
    #     self.previous_balance = latest_last_contract.previous_balance + total if latest_last_contract else self.previous_balance
    #     self.eos_indiminity = self.previous_balance + total_eos
    #     # return the result in line ids to show the
    #     # Create a dictionary with name and category from the salary rule
    #     computation_lines = [{
    #         'name': salary_rule_id.name,
    #         'category': salary_rule_id.category_id.name,
    #         # Set other fields to default values or leave them empty if needed
    #         'quantity': 1,
    #         'rate': self.eos_indiminity,
    #         'amount': self.eos_indiminity,
    #         'total': self.eos_indiminity,
    #         'employee_id': self.employee_id,  # Associate with the current wizard
    #         'date_start': self.date_start,  # Associate with the current wizard
    #         'date_end': self.date_end,  # Associate with the current wizard
    #         'previous_balance': self.previous_balance,  # Associate with the current wizard
    #         'eos_indiminity': self.eos_indiminity,  # Associate with the current wizard
    #     }]
    #
    #     self.write({
    #         'salary_computation_ids': [(0, 0, line) for line in computation_lines]
    #     })
    #     # self.salary_computation_ids = [(0, 0, line) for line in computation_lines]
    #     action = {
    #         'name': _('EOS Benefit Computation Results'),
    #         'view_mode': 'tree',
    #         'res_model': 'salary.computation.line',
    #         'type': 'ir.actions.act_window',
    #         'domain': [('employee_id', '=', self.employee_id)],
    #         'help': '<p class="o_view_nocontent_smiling_face">%s</p>' % _('No duplicates found')
    #     }
    #     return action


