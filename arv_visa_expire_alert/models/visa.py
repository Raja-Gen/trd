# -*- coding: utf-8 -*-
from odoo import models, fields


class HrEmployeeVisa(models.Model):
    _name = 'employee.visa.expire'
    _description = "Visa Expiry"
    _inherit = ['mail.thread', 'mail.activity.mixin']

    name = fields.Char('Employee')
    active = fields.Boolean('Active', default=True)
    employee_id = fields.Many2one('hr.employee', 'Employee')
    visa_expire = fields.Date('Visa Expire', related="employee_id.visa_expire")
    state = fields.Selection([('unsolve', 'Unsolved'), ('solve', 'Solved')], default="unsolve", string="State")
    activity_ids = fields.One2many('mail.activity', 'res_id', 'Activity')

    def open_employee_action(self):
        return {
            'name': "Employee",
            'type': 'ir.actions.act_window',
            'res_model': 'hr.employee',
            'res_id': self.employee_id.id,
            'view_mode': 'tree,form',
            'view_type': 'form',
            'views': [[False, 'form']],
            'target': 'current',
        }
