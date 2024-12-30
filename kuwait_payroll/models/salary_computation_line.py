from odoo import models, fields


class SalaryComputationLine(models.Model):
    _name = 'salary.computation.line'
    _description = 'Salary Computation'

    contract_id = fields.Many2one('hr.contract', string="Contract")
    currency_id = fields.Many2one(string="Currency", related='contract_id.currency_id')
    employee_id = fields.Many2one('hr.employee', string="Employee", related='contract_id.employee_id')
    date_start = fields.Date(string="Contract Start Date", required=True)
    date_end = fields.Date(string="Contract End Date", required=True)
    eos_indemnity = fields.Float(string="EOS Indemnity")
    name = fields.Char(string="Name")
    category = fields.Char(string="Category")
    quantity = fields.Float(string="Quantity")
    rate = fields.Float(string="Rate")
    amount = fields.Float(string="Amount")
    total = fields.Float(string="Total")
    salary_rule_id = fields.Many2one('hr.salary.rule', string='Salary Rule')
    struct_id = fields.Many2one('hr.payroll.structure', string='Structure', related='salary_rule_id.struct_id')
