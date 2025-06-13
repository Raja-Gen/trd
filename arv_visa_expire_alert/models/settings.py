# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ConfigSettings(models.TransientModel):
    _inherit = 'res.config.settings'

    arv_expiry_alert_day = fields.Integer('Days', config_parameter="arv_visa_expire_alert.arv_expiry_alert_day")
    arv_alert_user_id = fields.Many2one('res.users', string="Users")

    @api.model
    def get_values(self):
        res = super(ConfigSettings, self).get_values()
        params = self.env['ir.config_parameter'].sudo()
        arv_alert_user_id = params.get_param('arv_alert_user_id', default=False)
        res.update(arv_alert_user_id=int(arv_alert_user_id))
        return res

    def set_values(self):
        super(ConfigSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param("arv_alert_user_id",self.arv_alert_user_id.id)
