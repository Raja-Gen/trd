from email.policy import default

from odoo import models, fields

class AssignHrWizard(models.TransientModel):
    _name = 'assign.hr.wizard'
    _description = 'Assign HR Wizard'

    company_id = fields.Many2one('res.company', string='Company', default=lambda self: self.env.company,
        required=True)
    employee_ids = fields.Many2many('hr.employee', string='Employees',domain="[('company_id', '=', company_id)]")
    hr_employee_id = fields.Many2one('hr.employee', string='Assign to HR',domain="[('company_id', '=', company_id)]")

    def action_assign_hr(self):
        for employee in self.employee_ids:
            employee.hr_responsible_id = self.hr_employee_id.id