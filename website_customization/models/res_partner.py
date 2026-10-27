# -*- coding: utf-8 -*-
from odoo import api, fields, models


class ResPartner(models.Model):
    _inherit = "res.partner"

    website_pricelist_ids = fields.Many2many(
        "product.pricelist",
        "res_partner_website_pricelist_rel",
        "partner_id",
        "pricelist_id",
        string="Website Pricelists",
        help="Pricelists this customer can choose from on the website, on top of the "
             "public ones. Contacts of a company use the company's pricelists.",
    )
    allow_pay_on_account = fields.Boolean(
        string="Allow Pay on Account",
        company_dependent=True,
        help="The customer can place website orders against their credit limit "
             "instead of paying online.",
    )
    pay_on_account_credit_used = fields.Monetary(
        string="Used Credit",
        currency_field="currency_id",
        compute="_compute_pay_on_account_credit",
        groups="account.group_account_invoice,account.group_account_readonly",
        help="Unpaid invoices plus confirmed orders not invoiced yet.",
    )
    pay_on_account_credit_available = fields.Monetary(
        string="Available Credit",
        currency_field="currency_id",
        compute="_compute_pay_on_account_credit",
        groups="account.group_account_invoice,account.group_account_readonly",
        help="Credit limit minus credit used: what the customer can still order on account.",
    )
    is_ibuysafety_company = fields.Boolean(compute="_compute_is_ibuysafety_company")

    @api.depends_context("company")
    def _compute_pay_on_account_credit(self):
        company = self.env.company
        if not company.is_ibuysafety_company:
            self.pay_on_account_credit_used = 0.0
            self.pay_on_account_credit_available = 0.0
            return
        for partner in self:
            commercial = partner.commercial_partner_id.with_company(company).sudo()
            used = commercial._get_pay_on_account_credit_used(company)
            partner.pay_on_account_credit_used = used
            partner.pay_on_account_credit_available = commercial.credit_limit - used

    def _get_pay_on_account_credit_used(self, company):
        """Credit used by this commercial partner in `company`, in the company currency.

        Unpaid invoices plus confirmed orders not invoiced yet. Those orders count
        with their full total, not `amount_to_invoice`, which stays at 0 until the
        goods are delivered.
        """
        self.ensure_one()
        partner = self.with_company(company).sudo()
        today = fields.Date.context_today(self)
        open_orders = self.env['sale.order'].sudo().search([
            ('company_id', '=', company.id),
            ('state', '=', 'sale'),
            ('partner_id.commercial_partner_id', '=', partner.id),
        ])
        uninvoiced = sum(
            o.currency_id._convert(max(o.amount_total - o.amount_invoiced, 0.0), company.currency_id, company, today)
            for o in open_orders
        )
        return partner.credit + uninvoiced

    @api.depends_context("company")
    def _compute_is_ibuysafety_company(self):
        self.is_ibuysafety_company = self.env.company.is_ibuysafety_company
