# -*- coding: utf-8 -*-
from odoo import models, fields, api
from datetime import datetime, timedelta


class HrEmployee(models.Model):
    _inherit = 'hr.employee'

    visa_expire_ids = fields.One2many('employee.visa.expire', 'employee_id', 'Visa Expire')
    is_visa_late = fields.Boolean('Visa Late', compute="_is_visa_late")

    @api.depends('visa_expire_ids')
    def _is_visa_late(self):
        if self.visa_expire_ids:
            self.is_visa_late = True
        else:
            self.is_visa_late = False

    @api.onchange('visa_expire')
    def onchange_visa_expire(self):
        prior_day = self.env['ir.config_parameter'].sudo().get_param('arv_visa_expire_alert.arv_expiry_alert_day')
        current_date = datetime.now()
        prior_date = current_date + timedelta(days=int(prior_day))
        if self.visa_expire:
            date_diff = self.visa_expire - prior_date.date()
            if int(date_diff.days) > 0:
                self.visa_expire_ids.unlink()

    def check_visa_status(self):
        employee_ids = self.search([('active', '=', True), ('visa_expire', '!=', False)])
        all_visa = self.env['employee.visa.expire'].sudo().search([])
        if all_visa:
            all_visa.unlink()
        prior_day = self.env['ir.config_parameter'].sudo().get_param('arv_visa_expire_alert.arv_expiry_alert_day')
        user_id = self.env['ir.config_parameter'].sudo().get_param('arv_alert_user_id')
        visa_model_id = self.env['ir.model'].sudo().search([('model', '=', 'employee.visa.expire')], limit=1)
        if employee_ids:
            current_date = datetime.now()
            prior_date = current_date + timedelta(days=int(prior_day))
            for emp in employee_ids:
                date_diff = emp.visa_expire - prior_date.date()
                employee = self.env['employee.visa.expire'].sudo().search([('employee_id', '=', emp.id)])
                if int(date_diff.days) <= 0 and not employee:
                    created_visa = self.env['employee.visa.expire'].sudo().create(
                        {'employee_id': emp.id, 'visa_expire': emp.visa_expire, 'name': emp.name})
                    activity_ids = self.env['mail.activity'].sudo().create(
                        {'res_name': 'Visa Expiration', 'activity_type_id': 4, 'res_model_id': visa_model_id.id,
                         'res_model': visa_model_id.model, 'user_id': int(user_id), 'res_id': created_visa.id,
                         'summary': 'Visa Expiring Soon'})
                    created_visa.write({'activity_ids': [(4, activity_ids.id)]})
