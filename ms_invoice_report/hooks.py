# -*- coding: utf-8 -*-
from odoo import api, SUPERUSER_ID

BRAND_COMPANY_NAME = "MicroSolutions Kuwait"


def _flag_ms_company(env):
    """One-time bootstrap: tick the flag on the MicroSolutions company.

    Only used to seed the flag on install/upgrade; afterwards the checkbox on
    the company form is authoritative (so the company can be renamed freely).
    """
    company = env["res.company"].sudo().search(
        [("name", "=", BRAND_COMPANY_NAME)], limit=1)
    if company and not company.ms_invoice_brand:
        company.ms_invoice_brand = True


def post_init_hook(env_or_cr, registry=None):
    # Odoo 19 passes an Environment; keep the old (cr, registry) signature working.
    env = env_or_cr
    if registry is not None:
        env = api.Environment(env_or_cr, SUPERUSER_ID, {})
    _flag_ms_company(env)
