# -*- coding: utf-8 -*-

MS_COMPANY_NAME = "MicroSolutions Kuwait"


def post_init_hook(env):
    """One-time bootstrap: afterwards the checkbox on the company form decides."""
    company = env["res.company"].sudo().search([("name", "=", MS_COMPANY_NAME)], limit=1)
    if company:
        company.ms_project_portal = True
