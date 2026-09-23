# -*- coding: utf-8 -*-

import ast

from odoo import models, fields, api


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    # Fields
    activate_kpi = fields.Boolean(string="Activate KPI Report", config_parameter="business_kpi_report.activate_kpi")
    kpi_ids = fields.Many2many(
        "as.kpi", 
        string="KPIs", 
    )
    send_user_ids = fields.Many2many(
        "res.users",
        ondelete='restrict',
        string="Send To Users",
    )
    send_via = fields.Selection(
        [("sms", "SMS"), ("email", "Email")],
        string="Send Via",
        config_parameter="business_kpi_report.send_via",
    )
    duration = fields.Selection(
        [("day", "Day"), ("week", "Week"), ("month", "Month"), ("year", "Year")],
        string="Send Duration",
        config_parameter="business_kpi_report.duration",default='day',
    )
    email_template_id = fields.Many2one(
        "mail.template",
        string="KPI Email Template",
        config_parameter="business_kpi_report.email_template_id",
        default=lambda self: self.env.ref(
            "business_kpi_report.email_template_daily_kpi_report",
            raise_if_not_found=False,
        )
    )
    sms_template_id = fields.Many2one(
        "sms.template",
        string="KPI SMS Template",
        config_parameter="business_kpi_report.sms_template_id",
        default=lambda self: self.env.ref(
            "business_kpi_report.sms_template_daily_kpi_report",
            raise_if_not_found=False,
        )
    )
    company_ids = fields.Many2many('res.company', string="Companies", ondelete='restrict')

    # -----------------------------------------
    #  LOAD VALUES FROM CONFIG
    # -----------------------------------------
    @api.model
    def get_values(self):
        res = super().get_values()
        ICPSudo = self.env['ir.config_parameter'].sudo()

        kpi_ids_str = ICPSudo.get_param("business_kpi_report.kpi_ids")
        user_ids_str = ICPSudo.get_param("business_kpi_report.send_user_ids")
        company_ids_str = ICPSudo.get_param("business_kpi_report.company_ids")

        # ---- SAFE PARSING ----
        def safe_list(value):
            try:
                return ast.literal_eval(value) if value else []
            except Exception:
                return []  # fallback for invalid stored data

        kpi_ids = safe_list(kpi_ids_str)
        user_ids = safe_list(user_ids_str)
        company_ids = safe_list(company_ids_str)

        res.update(
            kpi_ids=[(6, 0, kpi_ids)],
            send_user_ids=[(6, 0, user_ids)],
            company_ids=[(6, 0, company_ids)],
        )
        return res

    # -----------------------------------------
    #  SAVE VALUES TO CONFIG
    # -----------------------------------------
    def set_values(self):
        super().set_values()

        ICPSudo = self.env['ir.config_parameter'].sudo()

        ICPSudo.set_param(
            "business_kpi_report.kpi_ids",
            self.kpi_ids.ids
        )

        ICPSudo.set_param(
            "business_kpi_report.send_user_ids",
            self.send_user_ids.ids
        )
        
        ICPSudo.set_param(
            "business_kpi_report.company_ids",
            self.company_ids.ids
        )

    
    def action_open_email_template(self):
        self.ensure_one()
        template = self.env.ref(
            "business_kpi_report.email_template_daily_kpi_report",
            raise_if_not_found=False
        )
        if not template:
            return
        return {
            "type": "ir.actions.act_window",
            "name": "Email Template",
            "res_model": "mail.template",
            "res_id": template.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_open_sms_template(self):
        self.ensure_one()
        template = self.env.ref(
            "business_kpi_report.sms_template_daily_kpi_report",
            raise_if_not_found=False
        )
        if not template:
            return
        return {
            "type": "ir.actions.act_window",
            "name": "SMS Template",
            "res_model": "sms.template",
            "res_id": template.id,
            "view_mode": "form",
            "target": "current",
        }