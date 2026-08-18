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
from odoo.exceptions import UserError, ValidationError


class DevPettyReplenish(models.Model):
    """
    Petty Cash Replenishment - tracks requests to add funds back to petty cash.
    Creates accounting entries from bank/source account to petty cash account.
    """
    _name = 'dev.petty.replenish'
    _description = 'Petty Cash Replenishment'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'requested_date desc, id desc'

    name = fields.Char(
        string='Reference',
        required=True,
        copy=False,
        readonly=True,
        default=lambda self: _('New'),
        index=True,
    )
    fund_id = fields.Many2one(
        'dev.petty.fund',
        string='Petty Cash Fund',
        required=True,
        ondelete='restrict',
        tracking=True,
        index=True,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        related='fund_id.company_id',
        store=True,
        readonly=True,
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='fund_id.currency_id',
        store=True,
        readonly=True,
    )
    requested_amount = fields.Monetary(
        string='Requested Amount',
        currency_field='currency_id',
        required=True,
        tracking=True,
    )
    requested_by = fields.Many2one(
        'res.users',
        string='Requested By',
        required=True,
        default=lambda self: self.env.user,
        tracking=True,
    )
    requested_date = fields.Datetime(
        string='Requested Date',
        required=True,
        default=fields.Datetime.now,
        tracking=True,
        index=True,
    )
    approved_by = fields.Many2one(
        'res.users',
        string='Approved By',
        readonly=True,
        copy=False,
        tracking=True,
    )
    approved_date = fields.Datetime(
        string='Approved Date',
        readonly=True,
        copy=False,
    )
    move_id = fields.Many2one(
        'account.move',
        string='Journal Entry',
        readonly=True,
        copy=False,
        help='The journal entry created for this replenishment.',
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('requested', 'Requested'),
        ('approved', 'Approved'),
        ('done', 'Done'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', required=True, tracking=True, index=True, copy=False)
    method = fields.Selection([
        ('manual', 'Manual'),
        ('auto', 'Automatic'),
    ], string='Request Method', default='manual', required=True,
        help='Manual: Requested by user. Auto: Triggered by threshold.')
    notes = fields.Text(
        string='Notes',
    )
    update_float = fields.Boolean(
        string='Update Fund Float',
        compute='_compute_update_float',
        store=True,
        readonly=False,
        help='If checked, the approved amount will be added to the Fund Float Amount upon completion.'
    )
    # Source account override (if different from fund default)
    source_journal_id = fields.Many2one(
        'account.journal',
        string='Source Journal',
        domain="[('type', 'in', ['bank', 'cash']), ('company_id', '=', company_id)]",
        help='Override the fund default replenishment journal.',
    )
    source_account_id = fields.Many2one(
        'account.account',
        string='Source Account',
        check_company=True,
        help='Override the fund default replenishment account.',
    )

    # ------------------
    # Compute Methods
    # ------------------
    @api.depends('requested_amount', 'fund_id')
    def _compute_update_float(self):
        """
        Automatically check 'Update Float' if requested amount > (Float - Available).
        This implies the user is asking for more money than is needed to just restore 
        the float, effectively increasing the fund size.
        """
        for record in self:
            if not record.fund_id:
                record.update_float = False
                continue
                
            # Calculate current deficit (amount needed to reach float capacity)
            current_deficit = record.fund_id.float_amount - record.fund_id.available_balance
            
            # If requesting significantly more than the deficit, assume it's a float increase
            # Using a small tolerance for floating point comparisons
            if record.requested_amount > (current_deficit + 0.01):
                record.update_float = True
            else:
                # Only Auto-uncheck if it was auto-checked? 
                # For now, let's keep it simple: if amount is normal, default to False
                # but allow user to override (since readonly=False in field def)
                # However, store=True compute fields with readonly=False can be tricky.
                # To support manual toggle, we should probably not force False here 
                # if the user manually set it. But `update_float` is a new field.
                record.update_float = False

    # ------------------
    # SQL Constraints
    # ------------------
    _sql_constraints = [
        ('amount_positive', 'CHECK(requested_amount > 0)',
         'Replenishment amount must be greater than zero.'),
    ]

    # ------------------
    # CRUD Methods
    # ------------------
    @api.model_create_multi
    def create(self, vals_list):
        """Generate sequence number on creation."""
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'dev.petty.replenish'
                ) or _('New')
        return super().create(vals_list)

    # ------------------
    # Action Methods
    # ------------------
    def action_request(self):
        """Submit replenishment request for approval."""
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_('Only draft requests can be submitted.'))

        self.write({'state': 'requested'})
        self.message_post(body=_('Replenishment request submitted for approval.'))

        # Send notification
        template = self.env.ref(
            'dev_petty_cash.email_template_replenish_requested',
            raise_if_not_found=False
        )
        if template:
            template.send_mail(self.id, force_send=True)

        return True

    def action_approve(self):
        """Approve the replenishment request."""
        self.ensure_one()
        if self.state != 'requested':
            raise UserError(_('Only requested replenishments can be approved.'))

        # Check permission
        if not self.env.user.has_group('dev_petty_cash.group_petty_manager'):
            raise UserError(_('Only Petty Cash Managers can approve replenishments.'))

        self.write({
            'state': 'approved',
            'approved_by': self.env.user.id,
            'approved_date': fields.Datetime.now(),
        })
        self.message_post(body=_('Replenishment approved by %s.') % self.env.user.name)
        return True

    def action_create_replenishment_move(self):
        """
        Create the journal entry for replenishment.

        Creates an account.move with:
        - Debit: Petty cash account (fund journal default account)
        - Credit: Bank/source account (replenishment source)

        Uses with_company() for proper multi-company context.
        """
        self.ensure_one()
        if self.state != 'approved':
            raise UserError(_('Only approved replenishments can create journal entries.'))

        # Determine source journal and account
        source_journal = self.source_journal_id or self.fund_id.replenish_journal_id
        source_account = self.source_account_id or self.fund_id.replenish_account_id

        if not source_journal:
            raise UserError(
                _('Please configure a replenishment journal on the fund or this request.')
            )
        if not source_account:
            raise UserError(
                _('Please configure a replenishment account on the fund or this request.')
            )

        # Get petty cash account from fund's journal
        petty_cash_journal = self.fund_id.journal_id
        petty_cash_account = (
            petty_cash_journal.default_account_id or
            petty_cash_journal.company_id.account_journal_payment_debit_account_id
        )
        if not petty_cash_account:
            raise UserError(
                _('Please configure a default account on the petty cash journal "%s".') %
                petty_cash_journal.name
            )

        # Create journal entry
        move_vals = {
            'move_type': 'entry',
            'journal_id': source_journal.id,
            'date': fields.Date.context_today(self),
            'ref': _('Petty Cash Replenishment - %s') % self.name,
            'company_id': self.company_id.id,
            'line_ids': [
                # Debit: Petty cash account (money coming in)
                (0, 0, {
                    'name': _('Petty Cash Replenishment - %s') % self.fund_id.name,
                    'account_id': petty_cash_account.id,
                    'debit': self.requested_amount,
                    'credit': 0.0,
                }),
                # Credit: Source/bank account (money going out)
                (0, 0, {
                    'name': _('Replenishment to %s') % self.fund_id.name,
                    'account_id': source_account.id,
                    'debit': 0.0,
                    'credit': self.requested_amount,
                }),
            ],
        }

        # Use with_company for multi-company safety
        move = self.env['account.move'].with_company(self.company_id).create(move_vals)

        # Post the move
        move.action_post()

        self.write({'move_id': move.id})
        self.message_post(
            body=_('Replenishment journal entry %s created and posted.') % move.name
        )

        return True

    float_increase_amount = fields.Monetary(
        string='Float Increase Amount',
        currency_field='currency_id',
        help='The portion of the replenishment that increased the fund float.',
    )

    def action_mark_done(self):
        """Mark replenishment as completed."""
        self.ensure_one()
        if self.state != 'approved':
            raise UserError(_('Only approved replenishments can be marked as done.'))
        if not self.move_id:
            raise UserError(
                _('Please create the journal entry before marking as done.')
            )

        # Calculate Float Increase Logic BEFORE changing state (so balance is 'before')
        increase_amount = 0.0
        if self.update_float:
            deficit = self.fund_id.float_amount - self.fund_id.available_balance
            if self.requested_amount > deficit:
                increase_amount = self.requested_amount - deficit
                # Update the replenishment record with the increase amount
                self.write({'float_increase_amount': increase_amount})
                
                # Update Fund Float
                self.fund_id.sudo().write({
                    'float_amount': self.fund_id.float_amount + increase_amount
                })
                self.message_post(
                    body=_('Fund Float Amount increased by %s (from surplus).') % increase_amount
                )

        self.write({'state': 'done'})
        self.message_post(body=_('Replenishment completed.'))

        # Trigger fund balance recompute
        self.fund_id._compute_available_balance()

        return True

    def unlink(self):
        """
        Handle deletion of replenishment requests.
        Strictly prevent deletion of non-draft/cancelled requests for all users.
        - Trigger recompute of fund balance.
        """
        for replenish in self:
            if replenish.state not in ('draft', 'cancelled'):
                raise UserError(
                    _('You cannot delete a replenishment that is not in draft or cancelled state.')
                )

        # Collect funds to recompute
        funds = self.mapped('fund_id')
        
        # User requested NOT to revert the float increase upon deletion.
        # So we simply remove the record and let the available balance recompute.
        
        res = super().unlink()
        
        # Force recompute of available balance for affected funds
        # This ensures that even if store=True lags, the value is updated immediately
        if funds:
            funds._compute_available_balance()
            
        return res

    def action_cancel(self):
        """Cancel the replenishment request."""
        self.ensure_one()
        if self.state == 'done':
            raise UserError(_('Completed replenishments cannot be cancelled.'))

        # If move exists and is posted, reverse it
        if self.move_id and self.move_id.state == 'posted':
            reversal = self.move_id._reverse_moves(
                default_values_list=[{
                    'ref': _('Reversal of %s - Replenishment Cancelled') % self.move_id.name,
                }],
                cancel=True,
            )
            self.message_post(
                body=_('Journal entry reversed: %s') % ', '.join(reversal.mapped('name'))
            )

        self.write({'state': 'cancelled'})
        self.message_post(body=_('Replenishment cancelled.'))
        return True

    def action_reset_to_draft(self):
        """Reset cancelled replenishment to draft."""
        self.ensure_one()
        if self.state != 'cancelled':
            raise UserError(_('Only cancelled requests can be reset to draft.'))
        self.write({
            'state': 'draft',
            'approved_by': False,
            'approved_date': False,
            'move_id': False,
        })
        self.message_post(body=_('Replenishment reset to draft.'))
        return True
