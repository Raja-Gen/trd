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
Voucher Extension for Policy Engine and Approval Matrix

This module extends dev.petty.voucher to integrate:
- Policy validation at request, approval, and payment stages
- Amount-based approval matrix with multi-level support
- Approval history tracking
"""

from odoo import api, fields, models, _
from odoo.exceptions import UserError, ValidationError


class DevPettyVoucherExtension(models.Model):
    """
    Extension of Petty Cash Voucher with Policy and Approval Matrix support.
    """
    _inherit = 'dev.petty.voucher'

    # ------------------
    # Policy Fields
    # ------------------
    policy_violation = fields.Boolean(
        string='Policy Violation',
        default=False,
        copy=False,
        tracking=True,
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
        tracking=True,
        help='Manager who approved the policy exception.',
    )
    policy_approved_date = fields.Datetime(
        string='Policy Exception Approved Date',
        copy=False,
    )

    # ------------------
    # Approval Matrix Fields
    # ------------------
    approval_level = fields.Integer(
        string='Current Approval Level',
        default=0,
        copy=False,
        help='Current approval level (0-indexed). Increments as approvals progress.',
    )
    total_approval_levels = fields.Integer(
        string='Total Approval Levels',
        default=1,
        copy=False,
        help='Total number of approval levels required.',
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
    pending_approval_level = fields.Char(
        string='Pending Approval',
        compute='_compute_pending_approval_level',
        help='Shows which approval level is pending.',
    )

    # ------------------
    # Compute Methods
    # ------------------
    @api.depends('approval_level', 'total_approval_levels', 'state')
    def _compute_pending_approval_level(self):
        """Compute display string for pending approval level."""
        for voucher in self:
            if voucher.state == 'requested':
                if voucher.total_approval_levels > 1:
                    voucher.pending_approval_level = _('Level %d of %d') % (
                        voucher.approval_level + 1,
                        voucher.total_approval_levels
                    )
                else:
                    voucher.pending_approval_level = _('Pending')
            else:
                voucher.pending_approval_level = ''

    # ------------------
    # Policy Validation Methods
    # ------------------
    def _validate_policies(self, stage='request'):
        """
        Validate voucher against all applicable policies.

        Args:
            stage: 'request', 'approve', 'pay', or 'reconcile'

        Raises:
            ValidationError if blocking violations occur
        """
        self.ensure_one()
        Policy = self.env['dev.petty.policy']

        try:
            result = Policy.validate_voucher_policies(self, stage)

            if result['requires_approval']:
                violation_notes = '\n'.join([
                    v['message'] for v in result['violations']
                ])
                self.write({
                    'policy_violation': True,
                    'policy_violation_notes': violation_notes,
                })
                self.message_post(
                    body=_('Policy violations detected:\n%s\n\nAdditional approval required.') %
                         violation_notes,
                    message_type='notification',
                )
        except ValidationError:
            raise

    def _clear_policy_violation(self):
        """Clear policy violation status after proper approval."""
        self.ensure_one()
        self.write({
            'policy_violation': False,
            'policy_violation_notes': False,
            'policy_approved_by_id': self.env.user.id,
            'policy_approved_date': fields.Datetime.now(),
        })

    # ------------------
    # Approval Matrix Methods
    # ------------------
    def _setup_approval_levels(self):
        """
        Setup approval levels based on approval matrix.
        Called when voucher is submitted for approval.
        """
        self.ensure_one()
        ApprovalMatrix = self.env['dev.petty.approval.matrix']

        try:
            approval_info = ApprovalMatrix.get_required_approvers(self)

            # Get unique sequences (levels)
            rules = approval_info['rules']
            sequences = sorted(set(rules.mapped('sequence')))
            total_levels = len(sequences)

            # Get approver groups for first level
            first_sequence = sequences[0] if sequences else 0
            first_level_rules = rules.filtered(lambda r: r.sequence == first_sequence)
            approver_groups = first_level_rules.mapped('approver_group_id')

            self.write({
                'approval_level': 0,
                'total_approval_levels': total_levels,
                'required_approver_group_ids': [(6, 0, approver_groups.ids)],
            })

            # Check for auto-approve
            if approval_info['can_auto_approve'] and not self.policy_violation:
                self._auto_approve()
                return True

            return False

        except UserError:
            # No approval rules configured - use legacy behavior
            self.write({
                'approval_level': 0,
                'total_approval_levels': 1,
                'required_approver_group_ids': [(5,)],
            })
            return False

    def _auto_approve(self):
        """Auto-approve voucher based on approval matrix configuration."""
        self.ensure_one()
        self.write({
            'state': 'approved',
            'approved_by_id': self.env.user.id,
            'approved_date': fields.Datetime.now(),
        })

        # Create approval history
        self.env['dev.petty.approval.history'].create({
            'voucher_id': self.id,
            'approval_level': 0,
            'approved_by_id': self.env.user.id,
            'action': 'approve',
            'notes': _('Auto-approved per approval matrix configuration.'),
        })

        self.message_post(body=_('Voucher auto-approved per approval matrix configuration.'))

    def _advance_approval_level(self):
        """
        Advance to next approval level.

        Returns:
            bool: True if there are more levels, False if fully approved
        """
        self.ensure_one()
        ApprovalMatrix = self.env['dev.petty.approval.matrix']

        try:
            approval_info = ApprovalMatrix.get_required_approvers(self)
        except UserError:
            return False

        rules = approval_info['rules']
        sequences = sorted(set(rules.mapped('sequence')))

        current_level = self.approval_level
        next_level = current_level + 1

        if next_level >= len(sequences):
            return False  # No more levels

        # Get next level rules and groups
        next_sequence = sequences[next_level]
        next_rules = rules.filtered(lambda r: r.sequence == next_sequence)
        approver_groups = next_rules.mapped('approver_group_id')

        self.write({
            'approval_level': next_level,
            'required_approver_group_ids': [(6, 0, approver_groups.ids)],
        })

        self.message_post(
            body=_('Voucher advanced to approval level %d of %d.') % (
                next_level + 1,
                self.total_approval_levels
            )
        )

        return True

    # ------------------
    # Overridden Action Methods
    # ------------------
    def action_request(self):
        """Submit voucher for approval with policy and matrix validation."""
        self.ensure_one()

        # Basic validations
        if self.state != 'draft':
            raise UserError(_('Only draft vouchers can be submitted for approval.'))
        if not self.line_ids:
            raise UserError(_('Please add at least one line item before submitting.'))
        if self.amount <= 0:
            raise UserError(_('Voucher amount must be greater than zero.'))
        if self.fund_id.state != 'active':
            raise UserError(_('Cannot submit voucher - the fund is blocked.'))

        # Validate policies
        self._validate_policies(stage='request')

        # Update state
        self.write({'state': 'requested'})

        # Setup approval levels
        auto_approved = self._setup_approval_levels()

        if not auto_approved:
            self.message_post(body=_('Voucher submitted for approval.'))

            # Send notification
            template = self.env.ref(
                'dev_petty_cash.email_template_voucher_requested',
                raise_if_not_found=False
            )
            if template:
                template.send_mail(self.id, force_send=True)

        return True

    def action_approve(self):
        """Approve the voucher with matrix and policy validation."""
        self.ensure_one()
        if self.state != 'requested':
            raise UserError(_('Only requested vouchers can be approved.'))

        ApprovalMatrix = self.env['dev.petty.approval.matrix']

        # Check if user can approve based on approval matrix
        try:
            can_approve_result = ApprovalMatrix.can_user_approve(self, self.env.user)

            if not can_approve_result['can_approve']:
                raise UserError(can_approve_result['reason'])

            # Check policy violation approval
            if self.policy_violation:
                if can_approve_result['is_policy_approver']:
                    self._clear_policy_violation()
                else:
                    raise UserError(
                        _('This voucher has policy violations. Only authorized approvers can approve it.')
                    )

        except UserError as e:
            # If no matrix configured, fall back to legacy behavior
            if 'No approval rules configured' in str(e):
                # Legacy permission check
                if not self.env.user.has_group('dev_petty_cash.group_petty_manager'):
                    if self.fund_id.responsible_user_id != self.env.user:
                        raise UserError(
                            _('You do not have permission to approve this voucher. '
                              'Only fund managers or the fund responsible can approve.')
                        )
            else:
                raise

        # Validate policies at approval stage
        self._validate_policies(stage='approve')

        # Check fund balance
        if self.amount > self.fund_id.available_balance:
            raise UserError(
                _('Insufficient fund balance. Available: %s, Requested: %s') % (
                    self.fund_id.currency_id.symbol + str(self.fund_id.available_balance),
                    self.fund_id.currency_id.symbol + str(self.amount),
                )
            )

        # Create approval history
        self.env['dev.petty.approval.history'].create({
            'voucher_id': self.id,
            'approval_level': self.approval_level,
            'approved_by_id': self.env.user.id,
            'action': 'approve',
        })

        # Check if more approval levels needed
        has_more_levels = self._advance_approval_level()

        if not has_more_levels:
            # Final approval
            self.write({
                'state': 'approved',
                'approved_by_id': self.env.user.id,
                'approved_date': fields.Datetime.now(),
            })
            self.message_post(body=_('Voucher approved by %s.') % self.env.user.name)

            # Send approval notification
            template = self.env.ref(
                'dev_petty_cash.email_template_voucher_approved',
                raise_if_not_found=False
            )
            if template:
                template.send_mail(self.id, force_send=True)
        else:
            self.message_post(
                body=_('Voucher approved by %s at level %d. Awaiting next level approval.') % (
                    self.env.user.name,
                    self.approval_level
                )
            )

        return True

    def action_pay(self):
        """Mark voucher as paid with policy validation."""
        self.ensure_one()

        # Validate policies at payment stage
        self._validate_policies(stage='pay')

        # Call parent implementation
        return super().action_pay()

    def action_reconcile(self):
        """Open reconciliation wizard with policy validation."""
        self.ensure_one()

        # Validate receipt policy at reconciliation stage
        self._validate_policies(stage='reconcile')

        # Call parent implementation
        return super().action_reconcile()

    # ------------------
    # Bulk Approval (from list view)
    # ------------------
    def _user_can_approve(self):
        """Whether the current user may approve THIS voucher at its current
        level, using the *same* rules as action_approve (approval matrix, or
        the legacy manager / fund-responsible fallback). Never raises - it is
        a silent pre-check used by the bulk action and by button visibility.
        """
        self.ensure_one()
        if self.state != 'requested':
            return False
        ApprovalMatrix = self.env['dev.petty.approval.matrix']
        try:
            result = ApprovalMatrix.can_user_approve(self, self.env.user)
            return bool(result.get('can_approve'))
        except UserError as e:
            # No matrix rule for this amount/company -> legacy permission check.
            if 'No approval rules configured' in str(e):
                return (
                    self.env.user.has_group('dev_petty_cash.group_petty_manager')
                    or self.fund_id.responsible_user_id == self.env.user
                )
            return False

    def action_approve_selected(self):
        """Approve several pending vouchers selected in the list view.

        Only the vouchers the current user is actually allowed to approve
        (per the current approval implementation) are processed; the others
        are skipped and reported. Each approval goes through the normal
        ``action_approve`` so every side effect (approval history, multi-level
        advancement, fund-balance and policy checks, notifications) is applied.
        A per-record savepoint keeps one failure from rolling back the rest.
        """
        approved = self.env['dev.petty.voucher']
        not_pending = self.env['dev.petty.voucher']
        no_permission = self.env['dev.petty.voucher']
        failed = []

        for voucher in self:
            if voucher.state != 'requested':
                not_pending |= voucher
                continue
            if not voucher._user_can_approve():
                no_permission |= voucher
                continue
            try:
                with self.env.cr.savepoint():
                    voucher.action_approve()
                approved |= voucher
            except (UserError, ValidationError) as e:
                failed.append('%s (%s)' % (voucher.name, e))

        parts = []
        if approved:
            parts.append(_('%d approved') % len(approved))
        if no_permission:
            parts.append(_('%d skipped - not an approver') % len(no_permission))
        if not_pending:
            parts.append(_('%d skipped - not pending') % len(not_pending))
        if failed:
            parts.append(_('%d failed: %s') % (len(failed), '; '.join(failed)))

        if approved and not (no_permission or not_pending or failed):
            notif_type = 'success'
        elif approved:
            notif_type = 'warning'
        else:
            notif_type = 'danger'

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Petty Cash Bulk Approval'),
                'message': ', '.join(parts) or _('Nothing to approve.'),
                'type': notif_type,
                'next': {'type': 'ir.actions.client', 'tag': 'soft_reload'},
            },
        }

    # ------------------
    # View Approval Info
    # ------------------
    def action_view_approval_history(self):
        """Open approval history for this voucher."""
        self.ensure_one()
        return {
            'name': _('Approval History'),
            'type': 'ir.actions.act_window',
            'res_model': 'dev.petty.approval.history',
            'view_mode': 'list,form',
            'domain': [('voucher_id', '=', self.id)],
            'context': {'default_voucher_id': self.id},
        }
