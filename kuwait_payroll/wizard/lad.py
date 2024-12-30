from odoo import models, fields, api
from odoo.exceptions import ValidationError
from odoo.tools.safe_eval import safe_eval


class Lad(models.TransientModel):
    _name = 'leave.advance.deduction'
    _description = 'Leave Advance Deduction'

    # contract_id = fields.Many2one('hr.contract', string="Contract", required=True)
    date_start = fields.Date(string="Start Date", required=True)
    date_end = fields.Date(string="End Date", required=True)
    employee_id = fields.Many2one('hr.employee', string="Employee", required=True)
    total_leaves = fields.Integer(string='Total Leaves', compute='_compute_total_leaves')
    total_amount = fields.Monetary(string='Total Amount',
        compute='_compute_total_amount')
    currency_id = fields.Many2one(
        'res.currency', default=lambda self: self.env.company.currency_id)
    show_post_journal = fields.Boolean('Show Post Journal', compute='_compute_show_post_journal')

    @api.depends('date_end', 'employee_id')
    def _compute_show_post_journal(self):
        if self.employee_id and self.date_end:
            expense_sheet = self.env['hr.expense.sheet'].sudo().search([('employee_id', 'in', self.employee_id.ids),
                                                                        ('state', '=', 'post'),
                                                                        ('date_end', '=', self.date_end)])
            if expense_sheet:
                self.show_post_journal = False
            else:
                self.show_post_journal = True
        else:
            self.show_post_journal = True

    @api.depends('total_leaves', 'date_start', 'date_end', 'employee_id')
    def _compute_total_amount(self):
        if self.employee_id and self.total_leaves and self.date_start and self.date_end:
            self.ensure_one()
            # Search for the salary rule defining the basic salary
            contract = self.env['hr.contract'].search([('employee_id', '=', self.employee_id.id)], order='id desc', limit=1)
            # payslip = self.env['hr.payslip'].search([('employee_id', '=', self.employee_id.id)], order='id desc',
            #                                           limit=1)
            if contract:
                basic_salary_rule = self.env['hr.salary.rule'].search([('code', '=', 'BASIC'),
                                                                       ('struct_id', '=', self.env.ref('kuwait_payroll.kuwait_employee_payroll_structure').id)
                                                                       ], limit=1)
                if not basic_salary_rule:
                    self.total_amount = 0
                    raise ValidationError('No BASIC salary rule found.')

                # Compute the basic salary based on the rule
                # This assumes you have a method or logic to compute the salary based on the rule
                localdict = {
                    'contract': contract,
                    'employee': self.employee_id,
                    'categories': {},
                    'rules': {},
                    'payslip': {},  # Placeholder for payslip context if needed
                    'worked_days': [],
                    'inputs': [],
                }
                basic_salary = 0.00
                if basic_salary_rule.amount_select == 'fix':
                    try:
                        basic_salary = basic_salary_rule.amount_fix or 0.0, float(safe_eval(basic_salary_rule.quantity, localdict)), 100.0
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
                if basic_salary > 0.00:
                    # worked_days = 0
                    # fetch_worked_days = payslip.worked_days_line_ids.filtered(lambda r: r.code == 'WORK100')
                    # if fetch_worked_days:
                    #     worked_days = fetch_worked_days.number_of_days

                    # total_working_days = worked_days + self.total_leaves
                    total_working_days = contract.basic_number_of_days
                    total_basic_salary = basic_salary #(payslip.contract_id.wage * basic_records.amount_percentage) / 100

                    if total_basic_salary and self.total_leaves > 0 and total_working_days > 0:
                        days = self.total_leaves / total_working_days  # 4/26 == 0.1538
                        lad = days * total_basic_salary  # lad
                        self.total_amount = lad
                    else:
                        self.total_amount = 0
                else:
                    self.total_amount = 0
            else:
                self.total_amount = 0
                raise ValidationError('No Contract found for this employee.')



        else:
            self.total_amount = 0

    @api.depends('date_start', 'date_end', 'employee_id')
    def _compute_total_leaves(self):
        if self.employee_id and self.date_start and self.date_end:
            leave_records = self.env['hr.leave'].search([
                ('employee_id', '=', self.employee_id.id),
                ('state', '=', 'validate'),
                ('request_date_from', '>=', self.date_start),
                ('request_date_to', '<=', self.date_end),
                ('holiday_status_id.time_type', '=', 'leave')  # Only consider leave type records
            ])
            # Calculate the total number of days absent
            self.total_leaves = sum(leave.number_of_days for leave in leave_records)
        else:
            self.total_leaves = 0

    def action_post_journal_entries(self):
        if not self.employee_id:
            raise ValidationError('Please select Employee.')
        if not self.total_leaves:
            raise ValidationError('No Leaves of the Employee.')
        if not self.total_amount:
            raise ValidationError('No LAD Amount of the Employee.')
        if not self.date_start or not self.date_end:
            raise ValidationError('Please make sure Both Date is selected.')

        # basic_records = self.env['hr.salary.rule'].search([
        #     ('code', '=', 'BASIC'),
        #     ('struct_id', '=', self.env.ref('kuwait_payroll.kuwait_employee_payroll_structure').id),
        # ], limit=1)
        # total_basic_salary = (self.contract_id.wage * basic_records.amount_percentage) / 100
        #
        # payslip = self.env['hr.payslip'].search([
        #     ('employee_id', '=', self.employee_id.id),
        #     ('contract_id', '=', self.contract_id.id),
        #     ('date_from', '>=', self.date_start),
        #     ('date_to', '<=', self.date_end)
        # ], limit=1)
        #
        # # Initialize working days
        # worked_days = 0
        # fetch_worked_days = payslip.worked_days_line_ids.filtered(lambda r: r.code == 'WORK100')
        # if fetch_worked_days:
        #     worked_days = fetch_worked_days.number_of_days
        #
        # total_working_days = worked_days + self.total_leaves
        #
        # if total_basic_salary and self.total_leaves > 0 and worked_days > 0 and total_working_days > 0:
        #     days = self.total_leaves / total_working_days  # 4/26 == 0.1538
        #     lad = days * total_basic_salary #lad
        product_a = self.env['product.product'].search([('name', '=', 'Others'), ('can_be_expensed', '=', True)
                                                        , ('detailed_type', '=', 'service')], limit=1)
        expense_sheet = self.env['hr.expense.sheet'].create({
            'name': str(self.employee_id.name)+' Leave Advance Deduction From '+str(self.date_start)+' To '+str(self.date_end),
            'employee_id': self.employee_id.id,
            'state': 'approve',
            'date_end': self.date_end,
            'accounting_date': self.date_end,
            'expense_line_ids': [(0, 0, {
                'name': 'Leave Advance Deduction '+str(self.total_leaves)+' Day(s) Leave.',
                'employee_id': self.employee_id.id,
                'product_id': product_a.id,
                'total_amount': self.total_amount,
                'total_amount_currency': self.total_amount,
                'price_unit': self.total_amount,
            })]
        })
        if expense_sheet:
            expense_sheet.action_sheet_move_create()
        else:
            raise ValidationError('Unknown error.')

    def action_next_payslip(self):
        if not self.employee_id:
            raise ValidationError('Please select Employee.')
        if not self.total_leaves:
            raise ValidationError('No Leaves of the Employee.')
        if not self.total_amount:
            raise ValidationError('No LAD Amount of the Employee.')
        if not self.date_start or not self.date_end:
            raise ValidationError('Please make sure Both Date is selected.')

        # basic_records = self.env['hr.salary.rule'].search([
        #     ('code', '=', 'BASIC'),
        #     ('struct_id', '=', self.env.ref('kuwait_payroll.kuwait_employee_payroll_structure').id),
        # ], limit=1)
        # total_basic_salary = (self.contract_id.wage * basic_records.amount_percentage) / 100
        #
        # payslip = self.env['hr.payslip'].search([
        #     ('employee_id', '=', self.employee_id.id),
        #     ('contract_id', '=', self.contract_id.id),
        #     ('date_from', '>=', self.date_start),
        #     ('date_to', '<=', self.date_end)
        # ], limit=1)
        #
        # # Initialize working days
        # worked_days = 0
        # fetch_worked_days = payslip.worked_days_line_ids.filtered(lambda r: r.code == 'WORK100')
        # if fetch_worked_days:
        #     worked_days = fetch_worked_days.number_of_days
        #
        # total_working_days = worked_days + self.total_leaves
        # if total_basic_salary and self.total_leaves > 0 and worked_days > 0 and total_working_days > 0:
        #     days = self.total_leaves / total_working_days  # 4/26 == 0.1538
        #     lad = days * total_basic_salary #lad
        product_a = self.env['product.product'].search([('name', '=', 'Others'), ('can_be_expensed', '=', True)
                                                        , ('detailed_type', '=', 'service')], limit=1)
        expense_sheet = self.env['hr.expense.sheet'].create({
            'name': str(self.employee_id.name)+' Leave Advance Deduction From '+str(self.date_start)+' To '+str(self.date_end),
            'employee_id': self.employee_id.id,
            'state': 'post',
            'date_end': self.date_end,
            'accounting_date': self.date_end,
            'expense_line_ids': [(0, 0, {
                'name': 'Leave Advance Deduction '+str(self.total_leaves)+' Day(s) Leave.',
                'employee_id': self.employee_id.id,
                'product_id': product_a.id,
                'total_amount': self.total_amount,
                'total_amount_company': self.total_amount,
                'unit_amount': self.total_amount,
            })]
        })
        if expense_sheet:
            expense_sheet.action_report_in_next_payslip()
        else:
            raise ValidationError('Unknown error.')
