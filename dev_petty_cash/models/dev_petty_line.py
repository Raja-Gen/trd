# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##############################################################################

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError


class DevPettyLine(models.Model):
    """
    Petty Cash Voucher Line - individual expense line items within a voucher.
    Supports products, custom descriptions, quantities, and accounting details.
    """
    _name = 'dev.petty.line'
    _description = 'Petty Cash Voucher Line'
    _order = 'voucher_id, sequence, id'

    voucher_id = fields.Many2one(
        'dev.petty.voucher',
        string='Voucher',
        required=True,
        ondelete='cascade',
        index=True,
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
    )
    product_id = fields.Many2one(
        'product.product',
        string='Product',
        help='Optional: Select a product to auto-fill description and account.',
    )
    description = fields.Char(
        string='Description',
        required=True,
    )
    quantity = fields.Float(
        string='Quantity',
        default=1.0,
        required=True,
    )
    price_unit = fields.Float(
        string='Unit Price',
        required=True,
        digits='Product Price',
    )
    subtotal = fields.Monetary(
        string='Subtotal',
        currency_field='currency_id',
        compute='_compute_subtotal',
        store=True,
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='voucher_id.currency_id',
        store=True,
        readonly=True,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        related='voucher_id.company_id',
        store=True,
        readonly=True,
    )
    account_id = fields.Many2one(
        'account.account',
        string='Expense Account',
        required=True,
        domain="[('account_type', 'in', ['expense', 'expense_depreciation', 'expense_direct_cost'])]",
        check_company=True,
        help='Account to debit for this expense.',
    )
    tax_ids = fields.Many2many(
        'account.tax',
        'dev_petty_line_tax_rel',
        'line_id',
        'tax_id',
        string='Taxes',
        domain="[('company_id', '=', company_id), ('type_tax_use', '=', 'purchase')]",
        help='Taxes applicable to this line (informational, not computed).',
    )
    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string='Analytic Account',
        help='Analytic account for cost tracking.',
    )

    # ------------------
    # SQL Constraints
    # ------------------
    _sql_constraints = [
        ('quantity_positive', 'CHECK(quantity > 0)',
         'Quantity must be greater than zero.'),
        ('price_unit_positive', 'CHECK(price_unit >= 0)',
         'Unit price must be non-negative.'),
    ]

    # ------------------
    # Compute Methods
    # ------------------
    @api.depends('quantity', 'price_unit')
    def _compute_subtotal(self):
        """Compute line subtotal."""
        for line in self:
            line.subtotal = line.quantity * line.price_unit

    # ------------------
    # Onchange Methods
    # ------------------
    @api.onchange('product_id')
    def _onchange_product_id(self):
        """Auto-fill description and account from product."""
        if self.product_id:
            self.description = self.product_id.display_name
            # Get expense account from product or category
            if self.product_id.property_account_expense_id:
                self.account_id = self.product_id.property_account_expense_id
            elif self.product_id.categ_id.property_account_expense_categ_id:
                self.account_id = self.product_id.categ_id.property_account_expense_categ_id
            # Set unit price from product standard price
            if self.product_id.standard_price:
                self.price_unit = self.product_id.standard_price

    @api.onchange('voucher_id')
    def _onchange_voucher_id(self):
        """Set default account from voucher's expense category."""
        if self.voucher_id and self.voucher_id.expense_category_id and not self.account_id:
            self.account_id = self.voucher_id.expense_category_id

    # ------------------
    # Validation
    # ------------------
    @api.constrains('account_id', 'company_id')
    def _check_account_company(self):
        """Ensure account belongs to the same company."""
        for line in self:
            if line.account_id and line.company_id not in line.account_id.company_ids:
                raise ValidationError(
                    _('The account "%s" belongs to a different company.') %
                    line.account_id.display_name
                )

    # @api.constrains('account_id', 'voucher_id')
    # def _check_allowed_expense_account(self):
    #     """
    #     Validate if the selected expense account is allowed by the fund's policies.
    #     """
    #     Policy = self.env['dev.petty.policy']
    #     for line in self:
    #         if not line.account_id or not line.voucher_id.fund_id:
    #             continue
                
    #         policies = Policy.get_applicable_policies(line.voucher_id.fund_id)
    #         for policy in policies:
    #             if policy.allowed_expense_account_ids and \
    #                line.account_id not in policy.allowed_expense_account_ids:
    #                 raise ValidationError(_(
    #                     'The expense account "%s" is not allowed for fund "%s" according to policy "%s". '
    #                     'Allowed accounts: %s'
    #                 ) % (
    #                     line.account_id.display_name,
    #                     line.voucher_id.fund_id.name,
    #                     policy.name,
    #                     ', '.join(policy.allowed_expense_account_ids.mapped('display_name'))
    #                 ))
