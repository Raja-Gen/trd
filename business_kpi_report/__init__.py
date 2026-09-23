# -*- coding: utf-8 -*-

from . import models


def uninstall_hook(env):
    params_to_remove = [
        "business_kpi_report.activate_kpi",
        "business_kpi_report.company_ids",
        "business_kpi_report.duration",
        "business_kpi_report.email_template_id",
        "business_kpi_report.kpi_ids",
        "business_kpi_report.send_user_ids",
        "business_kpi_report.sms_template_id",
        "business_kpi_report.send_via",
    ]

    env['ir.config_parameter'].sudo().search([
        ('key', 'in', params_to_remove)
    ]).unlink()