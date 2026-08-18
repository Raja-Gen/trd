# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##############################################################################

"""
Petty Cash Policy Engine

This module implements a flexible policy engine for petty cash management.
Policies can be configured per fund or globally (all funds) and enforce:
- Maximum voucher amounts
- Daily spending limits per user
- Receipt requirements above thresholds
- Allowed expense accounts

Policy violations can either block the transaction or require additional approval.
"""

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class DevPettyPolicy(models.Model):
    """
    Petty Cash Policy Configuration.

    Policies define rules and limits for petty cash transactions.
    They can be applied globally or to specific funds.
    """
    _name = 'dev.petty.policy'
    _description = 'Petty Cash Policy'
    _order = 'sequence, name'

    name = fields.Char(
        string='Policy Name',
        required=True,
        help='Descriptive name for this policy.',
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Order in which policies are evaluated (lower = first).',
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    fund_id = fields.Many2one(
        'dev.petty.fund',
        string='Fund',
        domain="[('company_id', '=', company_id)]",
        help='Leave empty to apply to all funds in this company.',
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='company_id.currency_id',
        readonly=True,
    )

    # Amount limits
    max_voucher_amount = fields.Monetary(
        string='Max Voucher Amount',
        currency_field='currency_id',
        help='Maximum amount allowed per voucher. Set to 0 for no limit.',
    )
    max_daily_amount_per_user = fields.Monetary(
        string='Max Daily Amount per User',
        currency_field='currency_id',
        help='Maximum total amount a user can request per day. Set to 0 for no limit.',
    )

    # Receipt requirements
    receipt_required_above = fields.Monetary(
        string='Receipt Required Above',
        currency_field='currency_id',
        help='Receipts are mandatory for vouchers above this amount. Set to 0 for always required.',
    )

    # Expense account restrictions
    allowed_expense_account_ids = fields.Many2many(
        'account.account',
        'dev_petty_policy_account_rel',
        'policy_id',
        'account_id',
        string='Allowed Expense Accounts',
        domain="[('account_type', 'in', ['expense', 'expense_depreciation', 'expense_direct_cost'])]",
        check_company=True,
        help='If set, only these expense accounts can be used. Leave empty for no restriction.',
    )

    # Violation handling
    violation_action = fields.Selection([
        ('block', 'Block Transaction'),
        ('require_approval', 'Require Additional Approval'),
    ], string='Violation Action', default='block', required=True,
        help='Block: Prevents the transaction entirely. '
             'Require Approval: Marks voucher for additional review.')

    active = fields.Boolean(
        string='Active',
        default=True,
    )

    # Tracking
    note = fields.Text(
        string='Notes',
        help='Additional notes about this policy.',
    )

    _sql_constraints = [
        ('max_voucher_positive', 'CHECK(max_voucher_amount >= 0)',
         'Maximum voucher amount must be non-negative.'),
        ('max_daily_positive', 'CHECK(max_daily_amount_per_user >= 0)',
         'Maximum daily amount must be non-negative.'),
        ('receipt_threshold_positive', 'CHECK(receipt_required_above >= 0)',
         'Receipt threshold must be non-negative.'),
    ]

    # ------------------
    # Policy Check Methods
    # ------------------
    @api.model
    def get_applicable_policies(self, fund):
        """
        Get all active policies applicable to a fund.

        Args:
            fund: dev.petty.fund record

        Returns:
            Recordset of applicable policies, ordered by sequence
        """
        return self.search([
            ('company_id', '=', fund.company_id.id),
            '|',
            ('fund_id', '=', fund.id),
            ('fund_id', '=', False),
            ('active', '=', True),
        ], order='sequence')

    def _check_policy_limits(self, voucher):
        """
        Check if voucher amount exceeds policy limits.

        Args:
            voucher: dev.petty.voucher record

        Returns:
            dict with 'violated': bool, 'message': str, 'policy': record
        """
        self.ensure_one()

        if self.max_voucher_amount > 0 and voucher.amount > self.max_voucher_amount:
            return {
                'violated': True,
                'message': _('Voucher amount %s exceeds maximum allowed %s per policy "%s".') % (
                    voucher.currency_id.symbol + str(voucher.amount),
                    voucher.currency_id.symbol + str(self.max_voucher_amount),
                    self.name,
                ),
                'policy': self,
            }
        return {'violated': False}

    def _check_daily_limit(self, voucher):
        """
        Check if user's daily spending limit is exceeded.

        Args:
            voucher: dev.petty.voucher record

        Returns:
            dict with 'violated': bool, 'message': str, 'policy': record
        """
        self.ensure_one()

        if self.max_daily_amount_per_user <= 0:
            return {'violated': False}

        # Calculate today's total for this user (excluding current voucher if it exists)
        today = fields.Date.today()
        domain = [
            ('requester_id', '=', voucher.requester_id.id),
            ('date', '=', today),
            ('state', 'not in', ['cancelled', 'draft']),
            ('company_id', '=', voucher.company_id.id),
        ]
        if voucher.id:
            domain.append(('id', '!=', voucher.id))

        # Use SQL for performance
        self.env.cr.execute("""
            SELECT COALESCE(SUM(amount), 0)
            FROM dev_petty_voucher
            WHERE requester_id = %s
                AND date = %s
                AND state NOT IN ('cancelled', 'draft')
                AND company_id = %s
                AND id != %s
        """, (voucher.requester_id.id, today, voucher.company_id.id, voucher.id or 0))

        daily_total = self.env.cr.fetchone()[0] or 0.0
        new_total = daily_total + voucher.amount

        if new_total > self.max_daily_amount_per_user:
            return {
                'violated': True,
                'message': _('Daily limit exceeded for user %s. '
                           'Today\'s total would be %s (limit: %s) per policy "%s".') % (
                    voucher.requester_id.name,
                    voucher.currency_id.symbol + str(new_total),
                    voucher.currency_id.symbol + str(self.max_daily_amount_per_user),
                    self.name,
                ),
                'policy': self,
            }
        return {'violated': False}

    def _check_receipt_compliance(self, voucher):
        """
        Check if receipts are required and present.

        Args:
            voucher: dev.petty.voucher record

        Returns:
            dict with 'violated': bool, 'message': str, 'policy': record
        """
        self.ensure_one()

        # Check only at reconciliation stage for paid vouchers
        if voucher.state != 'paid':
            return {'violated': False}

        if voucher.amount >= self.receipt_required_above:
            if not voucher.attachment_ids:
                return {
                    'violated': True,
                    'message': _('Receipts are required for vouchers of %s or more per policy "%s".') % (
                        voucher.currency_id.symbol + str(self.receipt_required_above),
                        self.name,
                    ),
                    'policy': self,
                }
        return {'violated': False}

    def _check_expense_accounts(self, voucher):
        """
        Check if voucher uses only allowed expense accounts.

        Args:
            voucher: dev.petty.voucher record

        Returns:
            dict with 'violated': bool, 'message': str, 'policy': record
        """
        self.ensure_one()

        if not self.allowed_expense_account_ids:
            return {'violated': False}

        voucher_accounts = voucher.line_ids.mapped('account_id')
        disallowed = voucher_accounts - self.allowed_expense_account_ids

        if disallowed:
            return {
                'violated': True,
                'message': _('Account(s) %s not allowed per policy "%s". '
                           'Allowed accounts: %s') % (
                    ', '.join(disallowed.mapped('display_name')),
                    self.name,
                    ', '.join(self.allowed_expense_account_ids.mapped('display_name')),
                ),
                'policy': self,
            }
        return {'violated': False}

    @api.model
    def validate_voucher_policies(self, voucher, stage='request'):
        """
        Validate a voucher against all applicable policies.

        Args:
            voucher: dev.petty.voucher record
            stage: 'request', 'approve', 'pay', or 'reconcile'

        Returns:
            dict with:
                'valid': bool
                'violations': list of violation dicts
                'requires_approval': bool (if any violation requires additional approval)

        Raises:
            ValidationError if any blocking violation occurs
        """
        policies = self.get_applicable_policies(voucher.fund_id)
        violations = []
        requires_approval = False

        for policy in policies:
            checks = []

            # Different checks for different stages
            if stage in ('request', 'approve'):
                checks.append(policy._check_policy_limits(voucher))
                checks.append(policy._check_daily_limit(voucher))
                checks.append(policy._check_expense_accounts(voucher))

            if stage == 'reconcile':
                checks.append(policy._check_receipt_compliance(voucher))

            for result in checks:
                if result.get('violated'):
                    if policy.violation_action == 'block':
                        raise ValidationError(result['message'])
                    else:
                        violations.append(result)
                        requires_approval = True

        return {
            'valid': len(violations) == 0,
            'violations': violations,
            'requires_approval': requires_approval,
        }


class DevPettyVoucherPolicyMixin(models.AbstractModel):
    """
    Mixin to add policy validation to vouchers.
    This is inherited by dev.petty.voucher.
    """
    _name = 'dev.petty.voucher.policy.mixin'
    _description = 'Voucher Policy Mixin'

    policy_violation = fields.Boolean(
        string='Policy Violation',
        default=False,
        copy=False,
        help='Indicates this voucher has policy violations requiring additional approval.',
    )
    policy_violation_notes = fields.Text(
        string='Policy Violation Notes',
        copy=False,
        help='Details of policy violations.',
    )
    policy_approved_by_id = fields.Many2one(
        'res.users',
        string='Policy Exception Approved By',
        copy=False,
        help='Manager who approved the policy exception.',
    )
    policy_approved_date = fields.Datetime(
        string='Policy Exception Approved Date',
        copy=False,
    )
