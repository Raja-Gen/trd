# -*- coding: utf-8 -*-

from odoo import models, api, fields
from odoo.exceptions import ValidationError

class HrLeave(models.Model):
    _inherit = 'hr.leave'


    @api.constrains('employee_id', 'holiday_status_id')
    def _check_maternity_leave_gender(self):
        """
        Ensure that maternity leave can only be requested by female employees.
        """
        for leave in self:
            leave_type = leave.holiday_status_id
            if leave_type.is_paid_maternity or leave_type.is_unpaid_maternity:
                employee_gender = leave.employee_id.gender
                if employee_gender != 'female':
                    raise ValidationError(
                        "Maternity Leave can only be requested by female employees."
                    )


    @api.constrains('holiday_status_id','request_date_from','request_date_to')
    def _check_maternity_leave_duration(self):
        """
        Constraint to ensure that maternity leave duration does not exceed the configured limits.
        """
        self.ensure_one()
        self._check_maternity_leave_gender()
        config = self.env['ir.config_parameter'].sudo()
        allow_paid = int(config.get_param('maternity_leave_salary.allow_paid_maternity_leave_days', default=70))
        allow_unpaid = int(config.get_param('maternity_leave_salary.allow_unpaid_maternity_leave_days', default=120))

        for leave in self:
            leave_type = leave.holiday_status_id
            leave_duration = leave.number_of_days_display or 0
            # Validate paid maternity leave duration
            if leave_type.is_paid_maternity and leave_duration > allow_paid:
                raise ValidationError(
                    "Paid Maternity Leave cannot exceed {} days. You have requested {} days.".format(allow_paid, leave_duration)
                )

            # Validate unpaid maternity leave duration
            if leave_type.is_unpaid_maternity and leave_duration > allow_unpaid:
                raise ValidationError(
                    "Unpaid Maternity Leave cannot exceed {} days. You have requested {} days.".format(allow_unpaid, leave_duration)
                )
