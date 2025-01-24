# -*- coding: utf-8 -*-

from odoo import models, api, exceptions, _

class HrLeave(models.Model):
    _inherit = 'hr.leave'

    @api.model
    def create(self, values):
        leave_type = self.env['hr.leave.type'].browse(values.get('holiday_status_id'))
        
        if leave_type.is_one_time_leave:
            employee = self.env['hr.employee'].browse(values.get('employee_id'))
            
            # Check if the employee has already used or been allocated this leave type
            existing_leave = self.env['hr.leave'].search([
                ('employee_id', '=', employee.id),
                ('holiday_status_id', '=', leave_type.id),
                ('state', 'in', ['confirm', 'validate', 'validate1'])
            ], limit=1)
            
            if existing_leave:
                raise exceptions.UserError(
                    _("You cannot request '%s' more than once.") % leave_type.name
                )
        
        return super(HrLeave, self).create(values)

