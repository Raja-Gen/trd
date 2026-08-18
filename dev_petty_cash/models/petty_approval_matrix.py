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
Petty Cash Approval Matrix

This module implements an amount-based and role-based approval matrix
for petty cash vouchers. Approval rules are configured with:
- Amount ranges (min/max)
- Approver groups
- Sequence for multi-level approval

The system automatically determines required approvers based on voucher amount
and enforces that the correct user group performs the approval.
"""

from odoo import api, fields, models, _
from odoo.exceptions import ValidationError, UserError


class DevPettyApprovalMatrix(models.Model):
    """
    Petty Cash Approval Matrix Configuration.

    Defines amount-based approval rules that determine which user groups
    can approve vouchers of specific amounts.
    """
    _name = 'dev.petty.approval.matrix'
    _description = 'Petty Cash Approval Matrix'
    _order = 'sequence, min_amount'

    name = fields.Char(
        string='Rule Name',
        required=True,
        help='Descriptive name for this approval rule.',
    )
    sequence = fields.Integer(
        string='Sequence',
        default=10,
        help='Order for multi-level approval. Lower sequence = first approver.',
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

    # Amount range
    min_amount = fields.Monetary(
        string='Minimum Amount',
        currency_field='currency_id',
        required=True,
        default=0.0,
        help='Minimum voucher amount for this rule to apply.',
    )
    max_amount = fields.Monetary(
        string='Maximum Amount',
        currency_field='currency_id',
        required=True,
        help='Maximum voucher amount for this rule to apply. Set to 0 for unlimited.',
    )

    # Approver configuration
    approver_group_id = fields.Many2one(
        'res.groups',
        string='Approver Group',
        required=True,
        help='Users in this group can approve vouchers matching this rule.',
    )
    auto_approve = fields.Boolean(
        string='Auto Approve',
        default=False,
        help='If checked, vouchers in this range are auto-approved without manual intervention.',
    )
    requires_policy_approval = fields.Boolean(
        string='Can Approve Policy Violations',
        default=False,
        help='If checked, this approver level can approve vouchers with policy violations.',
    )

    active = fields.Boolean(
        string='Active',
        default=True,
    )

    note = fields.Text(
        string='Notes',
        help='Additional notes about this approval rule.',
    )

    _sql_constraints = [
        ('amount_range_valid', 'CHECK(max_amount = 0 OR max_amount >= min_amount)',
         'Maximum amount must be greater than or equal to minimum amount (or 0 for unlimited).'),
        ('min_amount_positive', 'CHECK(min_amount >= 0)',
         'Minimum amount must be non-negative.'),
    ]

    @api.constrains('min_amount', 'max_amount', 'fund_id', 'company_id', 'active')
    def _check_overlapping_rules(self):
        """Check for overlapping amount ranges in the same fund/company."""
        for rule in self:
            if not rule.active:
                continue

            domain = [
                ('company_id', '=', rule.company_id.id),
                ('fund_id', '=', rule.fund_id.id),
                ('active', '=', True),
                ('id', '!=', rule.id),
            ]

            overlapping = self.search(domain)
            for other in overlapping:
                # Check for overlap
                rule_max = rule.max_amount or float('inf')
                other_max = other.max_amount or float('inf')

                if (rule.min_amount <= other_max and rule_max >= other.min_amount):
                    # Overlapping ranges - allowed only if different sequences (multi-level)
                    if rule.sequence == other.sequence:
                        raise ValidationError(
                            _('Overlapping amount ranges found with rule "%s". '
                              'Use different sequences for multi-level approval.') % other.name
                        )

    # ------------------
    # Approval Matrix Methods
    # ------------------
    @api.model
    def get_approval_rules(self, voucher):
        """
        Get all approval rules applicable to a voucher based on its amount.

        Args:
            voucher: dev.petty.voucher record

        Returns:
            Recordset of applicable approval rules, ordered by sequence
        """
        fund = voucher.fund_id
        amount = voucher.amount

        # Find all rules that match the amount range
        rules = self.search([
            ('company_id', '=', fund.company_id.id),
            '|',
            ('fund_id', '=', fund.id),
            ('fund_id', '=', False),
            ('active', '=', True),
            ('min_amount', '<=', amount),
            '|',
            ('max_amount', '=', 0),
            ('max_amount', '>=', amount),
        ], order='sequence, min_amount')

        return rules

    @api.model
    def get_required_approvers(self, voucher):
        """
        Get the required approver information for a voucher.

        Args:
            voucher: dev.petty.voucher record

        Returns:
            dict with:
                'rules': recordset of applicable rules
                'current_level': int (current approval level, 0-indexed)
                'total_levels': int
                'current_rule': current rule to apply
                'can_auto_approve': bool
                'approver_groups': list of group records
        """
        rules = self.get_approval_rules(voucher)

        if not rules:
            raise UserError(
                _('No approval rules configured for voucher amount %s. '
                  'Please configure approval matrix for this amount range.') %
                (voucher.currency_id.symbol + str(voucher.amount))
            )

        # Group by sequence to get approval levels
        levels = {}
        for rule in rules:
            if rule.sequence not in levels:
                levels[rule.sequence] = []
            levels[rule.sequence].append(rule)

        sorted_levels = sorted(levels.keys())
        total_levels = len(sorted_levels)

        # Determine current approval level from voucher
        current_level = voucher.approval_level if hasattr(voucher, 'approval_level') else 0

        if current_level >= total_levels:
            current_level = total_levels - 1

        current_sequence = sorted_levels[current_level] if sorted_levels else 0
        current_rules = levels.get(current_sequence, [])

        # Check if all current rules allow auto-approve
        can_auto_approve = all(r.auto_approve for r in current_rules) if current_rules else False

        # Get all approver groups for current level
        approver_groups = self.env['res.groups']
        for rule in current_rules:
            approver_groups |= rule.approver_group_id

        return {
            'rules': rules,
            'current_level': current_level,
            'total_levels': total_levels,
            'current_rules': self.browse([r.id for r in current_rules]),
            'can_auto_approve': can_auto_approve,
            'approver_groups': approver_groups,
            'next_level_exists': current_level + 1 < total_levels,
        }

    @api.model
    def can_user_approve(self, voucher, user=None):
        """
        Check if a user can approve a specific voucher.

        Args:
            voucher: dev.petty.voucher record
            user: res.users record (defaults to current user)

        Returns:
            dict with:
                'can_approve': bool
                'reason': str (if cannot approve)
                'is_policy_approver': bool (can approve policy violations)
        """
        if user is None:
            user = self.env.user

        approval_info = self.get_required_approvers(voucher)
        current_rules = approval_info.get('current_rules', self.browse())

        if not current_rules:
            return {
                'can_approve': False,
                'reason': _('No approval rules found for this voucher amount.'),
                'is_policy_approver': False,
            }

        # Check if user belongs to any approver group
        user_groups = user.all_group_ids
        can_approve = False
        is_policy_approver = False

        for rule in current_rules:
            if rule.approver_group_id in user_groups:
                can_approve = True
                if rule.requires_policy_approval:
                    is_policy_approver = True

        if not can_approve:
            group_names = ', '.join(current_rules.mapped('approver_group_id.name'))
            return {
                'can_approve': False,
                'reason': _('You must belong to one of these groups to approve: %s') % group_names,
                'is_policy_approver': False,
            }

        # Check if voucher has policy violations and user can approve them
        if voucher.policy_violation and not is_policy_approver:
            return {
                'can_approve': False,
                'reason': _('This voucher has policy violations. Only authorized approvers can process it.'),
                'is_policy_approver': False,
            }

        return {
            'can_approve': True,
            'reason': '',
            'is_policy_approver': is_policy_approver,
        }


class DevPettyVoucherApprovalMixin(models.AbstractModel):
    """
    Mixin to add approval matrix fields to vouchers.
    This is inherited by dev.petty.voucher.
    """
    _name = 'dev.petty.voucher.approval.mixin'
    _description = 'Voucher Approval Mixin'

    approval_level = fields.Integer(
        string='Approval Level',
        default=0,
        copy=False,
        help='Current approval level (0-indexed). Increments as approvals progress.',
    )
    required_approver_group_ids = fields.Many2many(
        'res.groups',
        'dev_petty_voucher_required_approver_rel',
        'voucher_id',
        'group_id',
        string='Required Approver Groups',
        copy=False,
        help='Groups that can approve this voucher at current level.',
    )
    approval_history_ids = fields.One2many(
        'dev.petty.approval.history',
        'voucher_id',
        string='Approval History',
        copy=False,
    )
    total_approval_levels = fields.Integer(
        string='Total Approval Levels',
        default=1,
        copy=False,
    )


class DevPettyApprovalHistory(models.Model):
    """
    Tracks approval history for vouchers.
    """
    _name = 'dev.petty.approval.history'
    _description = 'Petty Cash Approval History'
    _order = 'create_date desc'

    voucher_id = fields.Many2one(
        'dev.petty.voucher',
        string='Voucher',
        required=True,
        ondelete='cascade',
        index=True,
    )
    approval_level = fields.Integer(
        string='Approval Level',
        required=True,
    )
    approved_by_id = fields.Many2one(
        'res.users',
        string='Approved By',
        required=True,
        default=lambda self: self.env.user,
    )
    approval_date = fields.Datetime(
        string='Approval Date',
        required=True,
        default=fields.Datetime.now,
    )
    rule_id = fields.Many2one(
        'dev.petty.approval.matrix',
        string='Approval Rule',
    )
    notes = fields.Text(
        string='Notes',
    )
    action = fields.Selection([
        ('approve', 'Approved'),
        ('reject', 'Rejected'),
        ('escalate', 'Escalated'),
    ], string='Action', required=True, default='approve')
