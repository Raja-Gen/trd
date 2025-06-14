# -*- coding: utf-8 -*-
# Part of Probuse Consulting Service Pvt Ltd.
# See LICENSE file for full copyright and licensing details.

from odoo import api, fields, models


class Users(models.Model):
    _inherit = "res.users"

    # @api.multi
    def action_view_user(self):
        self.ensure_one()
        action = self.env.ref('odoo_licences_certificates.licences_certificate_action').sudo().read()[0]
        action['domain'] = str([('user_id', 'in', self.ids)])
        return action

    # @api.multi
    def action_view_user_history(self):
        self.ensure_one()
        action = self.env.ref('odoo_licences_certificates.record_licences_action_add').sudo().read()[0]
        action['domain'] = str([('user_id', 'in', self.ids)])
        return action
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: