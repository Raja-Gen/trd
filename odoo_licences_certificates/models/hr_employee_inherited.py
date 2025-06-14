# -*- coding: utf-8 -*-
# Part of Probuse Consulting Service Pvt Ltd.
# See LICENSE file for full copyright and licensing details.


from odoo import models, fields,api
class HrEmployee(models.Model):
    _inherit = "hr.employee"


    # @api.multi
    def action_view_employee(self):
        self.ensure_one()
        action = self.env.ref('odoo_licences_certificates.licences_certificate_action').sudo().read()[0]
        action['domain'] = str([('employee_id', 'in', self.ids)])
        return action

    # @api.multi
    def action_view_employee_history(self):
        self.ensure_one()
        action = self.env.ref('odoo_licences_certificates.record_licences_action_add').sudo().read()[0]
        action['domain'] = str([('employee_id', 'in', self.ids)])
        return action
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: