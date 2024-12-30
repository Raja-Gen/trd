# -*- coding: utf-8 -*-
from odoo import api, fields, models
from odoo.osv import expression


class HrPayslipEmployees(models.TransientModel):
    _inherit = 'hr.payslip.employees'
    _description = 'Generate payslips for all selected employees'

    @api.depends('structure_id', 'department_id')
    def _compute_employee_ids(self):
        for wizard in self:
            domain = wizard._get_available_contracts_domain()
            if wizard.structure_id and wizard.structure_id.type_id:
                employees_contract = self.env['hr.contract'].sudo().search_read([('structure_type_id', '=', wizard.structure_id.type_id.id)], ['employee_id'])
                employee_ids = [e['employee_id'][0] for e in employees_contract if e['employee_id']]
                domain = expression.AND([
                    domain,
                    [('id', 'in', employee_ids)]
                ])
            elif wizard.department_id:
                domain = expression.AND([
                    domain,
                    [('department_id', 'child_of', self.department_id.id)]
                ])
            wizard.employee_ids = self.env['hr.employee'].search(domain)
