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


class DevPettyVoucher(models.Model):
    """
    Petty Cash Voucher - represents a request for petty cash disbursement.
    Follows workflow: draft -> requested -> approved -> paid -> reconciled
    """
    _name = 'dev.petty.voucher'
    _description = 'Petty Cash Voucher'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'date desc, id desc'

    # ------------------
    # Database Indexes for Performance
    # ------------------
    # Indexes on: fund_id, state, date (via index=True)

    name = fields.Char(
        string='Voucher Number',
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
        domain="[('state', '=', 'active'), ('company_id', '=', company_id)]",
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        index=True,
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='fund_id.currency_id',
        store=True,
        readonly=True,
    )
    requester_id = fields.Many2one(
        'res.users',
        string='Requester',
        required=True,
        default=lambda self: self.env.user,
        tracking=True,
    )
    requester_employee_id = fields.Many2one(
        'hr.employee',
        string='Employee',
        compute='_compute_requester_employee',
        store=True,
        help='Employee record linked to the requester user.',
    )
    date = fields.Date(
        string='Date',
        required=True,
        default=fields.Date.context_today,
        tracking=True,
        index=True,
    )
    amount = fields.Monetary(
        string='Total Amount',
        currency_field='currency_id',
        compute='_compute_amount',
        store=True,
        tracking=True,
    )
    purpose = fields.Text(
        string='Purpose/Description',
        required=True,
        tracking=True,
        help='Describe the purpose of this petty cash request.',
    )
    expense_category_id = fields.Many2one(
        'account.account',
        string='Default Expense Account',
        domain="[('account_type', 'in', ['expense', 'expense_depreciation', 'expense_direct_cost'])]",
        check_company=True,
        help='Default expense account for this voucher. Can be overridden per line.',
    )
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'dev_petty_voucher_attachment_rel',
        'voucher_id',
        'attachment_id',
        string='Attachments',
        help='Attach receipts and supporting documents.',
    )
    state = fields.Selection([
        ('draft', 'Draft'),
        ('requested', 'Requested'),
        ('approved', 'Approved'),
        ('paid', 'Paid'),
        ('reconciled', 'Reconciled'),
        ('cancelled', 'Cancelled'),
    ], string='Status', default='draft', required=True, tracking=True, index=True, copy=False)

    approved_by_id = fields.Many2one(
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
    paid_by_id = fields.Many2one(
        'res.users',
        string='Paid By',
        readonly=True,
        copy=False,
        tracking=True,
    )
    paid_date = fields.Datetime(
        string='Paid Date',
        readonly=True,
        copy=False,
    )
    payment_move_id = fields.Many2one(
        'account.move',
        string='Payment Journal Entry',
        readonly=True,
        copy=False,
        help='The journal entry created when this voucher was paid.',
    )
    line_ids = fields.One2many(
        'dev.petty.line',
        'voucher_id',
        string='Voucher Lines',
        copy=True,
    )
    # Analytic accounting (optional, works if analytic module is installed)
    analytic_account_id = fields.Many2one(
        'account.analytic.account',
        string='Analytic Account',
        help='Default analytic account for this voucher.',
    )
    # Additional tracking fields
    receipt_total = fields.Monetary(
        string='Receipt Total',
        currency_field='currency_id',
        help='Total amount from attached receipts (entered during reconciliation).',
    )
    variance_amount = fields.Monetary(
        string='Variance',
        currency_field='currency_id',
        compute='_compute_variance',
        store=True,
        help='Difference between paid amount and receipt total.',
    )
    variance_move_id = fields.Many2one(
        'account.move',
        string='Variance Journal Entry',
        readonly=True,
        copy=False,
    )

    # ------------------
    # SQL Constraints
    # ------------------
    _sql_constraints = [
        ('amount_positive', 'CHECK(amount >= 0)',
         'Voucher amount must be non-negative.'),
        ('name_unique', 'UNIQUE(name, company_id)',
         'Voucher number must be unique per company.'),
    ]

    # ------------------
    # Constraints
    # ------------------
    @api.constrains('fund_id', 'company_id')
    def _check_fund_company(self):
        """Ensure fund belongs to the same company as the voucher."""
        for voucher in self:
            if voucher.fund_id and voucher.fund_id.company_id != voucher.company_id:
                raise ValidationError(
                    _('The selected fund belongs to a different company. '
                      'Please select a fund from the same company.')
                )

    @api.constrains('amount', 'fund_id')
    def _check_amount_vs_balance(self):
        """Warn if amount exceeds available fund balance."""
        for voucher in self:
            if voucher.state == 'draft' and voucher.amount > voucher.fund_id.available_balance:
                # Just a warning in draft, will be enforced at approval
                pass

    @api.constrains('expense_category_id', 'fund_id')
    def _check_default_expense_account(self):
        """
        Validate if the default expense account is allowed by the fund's policies.
        """
        Policy = self.env['dev.petty.policy']
        for voucher in self:
            if not voucher.expense_category_id or not voucher.fund_id:
                continue
                
            policies = Policy.get_applicable_policies(voucher.fund_id)
            for policy in policies:
                if policy.allowed_expense_account_ids and \
                   voucher.expense_category_id not in policy.allowed_expense_account_ids:
                    raise ValidationError(_(
                        'The default expense account "%s" is not allowed for fund "%s" according to policy "%s". '
                        'Allowed accounts: %s'
                    ) % (
                        voucher.expense_category_id.display_name,
                        voucher.fund_id.name,
                        policy.name,
                        ', '.join(policy.allowed_expense_account_ids.mapped('display_name'))
                    ))
    # ------------------
    # Compute Methods
    # ------------------
    @api.depends('requester_id')
    def _compute_requester_employee(self):
        """Find the employee record for the requester user."""
        for voucher in self:
            employee = self.env['hr.employee'].search([
                ('user_id', '=', voucher.requester_id.id),
                ('company_id', '=', voucher.company_id.id),
            ], limit=1)
            voucher.requester_employee_id = employee

    @api.depends('line_ids.subtotal')
    def _compute_amount(self):
        """Compute total amount from lines."""
        for voucher in self:
            voucher.amount = sum(voucher.line_ids.mapped('subtotal'))

    @api.depends('amount', 'receipt_total')
    def _compute_variance(self):
        """Compute variance between amount paid and receipts."""
        for voucher in self:
            if voucher.receipt_total:
                voucher.variance_amount = voucher.amount - voucher.receipt_total
            else:
                voucher.variance_amount = 0.0

    # ------------------
    # CRUD Methods
    # ------------------
    @api.model_create_multi
    def create(self, vals_list):
        """Generate sequence number on creation."""
        for vals in vals_list:
            if vals.get('name', _('New')) == _('New'):
                vals['name'] = self.env['ir.sequence'].next_by_code(
                    'dev.petty.voucher'
                ) or _('New')
        return super().create(vals_list)

    def unlink(self):
        """
        Handle deletion of vouchers.
        Strictly prevent deletion of non-draft vouchers for ALL users.
        User must cancel the voucher first, which handles accounting reversals.
        """
        for voucher in self:
            if voucher.state not in ('draft', 'cancelled'):
                raise UserError(
                    _('You cannot delete a voucher that is not in draft or cancelled state.')
                )
        return super().unlink()

    # ------------------
    # Onchange Methods
    # ------------------
    @api.onchange('fund_id')
    def _onchange_fund_id(self):
        """Update company and currency when fund changes."""
        if self.fund_id:
            self.company_id = self.fund_id.company_id

    @api.onchange('expense_category_id')
    def _onchange_expense_category(self):
        """Update lines with default expense account."""
        if self.expense_category_id:
            for line in self.line_ids:
                if not line.account_id:
                    line.account_id = self.expense_category_id

    # ------------------
    # Action Methods
    # ------------------
    def action_request(self):
        """Submit voucher for approval."""
        self.ensure_one()
        if self.state != 'draft':
            raise UserError(_('Only draft vouchers can be submitted for approval.'))
        if not self.line_ids:
            raise UserError(_('Please add at least one line item before submitting.'))
        if self.amount <= 0:
            raise UserError(_('Voucher amount must be greater than zero.'))
        if self.fund_id.state != 'active':
            raise UserError(_('Cannot submit voucher - the fund is blocked.'))

        self.write({'state': 'requested'})
        self.message_post(body=_('Voucher submitted for approval.'))

        # Send notification to fund responsible
        template = self.env.ref(
            'dev_petty_cash.email_template_voucher_requested',
            raise_if_not_found=False
        )
        if template:
            template.send_mail(self.id, force_send=True)

        return True

    def action_approve(self):
        """Approve the voucher request."""
        self.ensure_one()
        if self.state != 'requested':
            raise UserError(_('Only requested vouchers can be approved.'))

        # Check if approver has permission (manager or fund responsible)
        if not self.env.user.has_group('dev_petty_cash.group_petty_manager'):
            if self.fund_id.responsible_user_id != self.env.user:
                raise UserError(
                    _('You do not have permission to approve this voucher. '
                      'Only fund managers or the fund responsible can approve.')
                )

        # Check fund balance
        if self.amount > self.fund_id.available_balance:
            raise UserError(
                _('Insufficient fund balance. Available: %s, Requested: %s') % (
                    self.fund_id.currency_id.symbol + str(self.fund_id.available_balance),
                    self.fund_id.currency_id.symbol + str(self.amount),
                )
            )

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

        return True

    def action_pay(self):
        """
        Mark voucher as paid and create the journal entry.

        Creates an account.move with:
        - Debit: Expense accounts (from line items)
        - Credit: Petty cash account (from journal)

        Uses with_company() for proper multi-company context.
        """
        self.ensure_one()
        if self.state != 'approved':
            raise UserError(_('Only approved vouchers can be paid.'))

        # Validate lines have accounts
        for line in self.line_ids:
            if not line.account_id:
                raise UserError(
                    _('Line "%s" is missing an expense account. '
                      'Please set the account before payment.') % line.description
                )

        # Get petty cash account from journal
        journal = self.fund_id.journal_id
        petty_cash_account = (
            journal.default_account_id or
            journal.company_id.account_journal_payment_credit_account_id
        )
        if not petty_cash_account:
            raise UserError(
                _('Please configure a default account on the petty cash journal "%s".') %
                journal.name
            )

        # Create journal entry with proper company context
        move_vals = self._prepare_payment_move_vals(petty_cash_account)

        # Use with_company for multi-company safety
        move = self.env['account.move'].with_company(self.company_id).create(move_vals)

        # Post the move
        move.action_post()

        self.write({
            'state': 'paid',
            'paid_by_id': self.env.user.id,
            'paid_date': fields.Datetime.now(),
            'payment_move_id': move.id,
        })

        self.message_post(
            body=_('Voucher paid. Journal entry %s created and posted.') % move.name
        )

        # Send payment notification
        template = self.env.ref(
            'dev_petty_cash.email_template_voucher_paid',
            raise_if_not_found=False
        )
        if template:
            template.send_mail(self.id, force_send=True)

        return True

    def _prepare_payment_move_vals(self, petty_cash_account):
        """
        Prepare values for the payment journal entry.

        Returns dict for account.move creation with:
        - Debit lines for each expense line item
        - Credit line for petty cash account
        """
        self.ensure_one()

        move_lines = []

        # Debit lines - expenses
        for line in self.line_ids:
            line_vals = {
                'name': line.description or self.purpose,
                'account_id': line.account_id.id,
                'debit': line.subtotal,
                'credit': 0.0,
                'partner_id': self.requester_id.partner_id.id,
            }
            # Add analytic if available
            if line.analytic_account_id or self.analytic_account_id:
                analytic = line.analytic_account_id or self.analytic_account_id
                line_vals['analytic_distribution'] = {str(analytic.id): 100}
            move_lines.append((0, 0, line_vals))

        # Credit line - petty cash
        move_lines.append((0, 0, {
            'name': _('Petty Cash Disbursement - %s') % self.name,
            'account_id': petty_cash_account.id,
            'debit': 0.0,
            'credit': self.amount,
        }))

        return {
            'move_type': 'entry',
            'journal_id': self.fund_id.journal_id.id,
            'date': self.date,
            'ref': self.name,
            'company_id': self.company_id.id,
            'line_ids': move_lines,
        }

    def action_reconcile(self):
        """
        Open the reconciliation wizard to upload receipts and reconcile.
        """
        self.ensure_one()
        if self.state != 'paid':
            raise UserError(_('Only paid vouchers can be reconciled.'))

        return {
            'name': _('Reconcile Voucher'),
            'type': 'ir.actions.act_window',
            'res_model': 'petty.cash.reconcile.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_voucher_id': self.id,
                'default_paid_amount': self.amount,
            },
        }

    def action_mark_reconciled(self, receipt_total, variance_move=None):
        """
        Mark voucher as reconciled (called from wizard).

        Args:
            receipt_total: Total amount from receipts
            variance_move: Optional account.move for variance adjustment
        """
        self.ensure_one()
        vals = {
            'state': 'reconciled',
            'receipt_total': receipt_total,
        }
        if variance_move:
            vals['variance_move_id'] = variance_move.id

        self.write(vals)
        self.message_post(
            body=_('Voucher reconciled. Receipt total: %s, Variance: %s') % (
                self.currency_id.symbol + str(receipt_total),
                self.currency_id.symbol + str(self.variance_amount),
            )
        )
        return True

    def action_cancel(self):
        """Cancel the voucher."""
        self.ensure_one()
        if self.state in ('reconciled',):
            raise UserError(_('Reconciled vouchers cannot be cancelled.'))

        # If paid, we need to reverse the journal entry
        if self.state == 'paid' and self.payment_move_id:
            if self.payment_move_id.state == 'posted':
                # Create reversal
                reversal = self.payment_move_id._reverse_moves(
                    default_values_list=[{
                        'ref': _('Reversal of %s - Voucher Cancelled') % self.payment_move_id.name,
                    }],
                    cancel=True,
                )
                self.message_post(
                    body=_('Payment reversed. Reversal entry: %s') %
                    ', '.join(reversal.mapped('name'))
                )

        self.write({'state': 'cancelled'})
        self.message_post(body=_('Voucher cancelled.'))
        return True

    def action_reset_to_draft(self):
        """Reset cancelled voucher to draft."""
        self.ensure_one()
        if self.state != 'cancelled':
            raise UserError(_('Only cancelled vouchers can be reset to draft.'))
        self.write({'state': 'draft'})
        self.message_post(body=_('Voucher reset to draft.'))
        return True

    # ------------------
    # Report Methods
    # ------------------
    def action_print_voucher(self):
        """Print the voucher report."""
        self.ensure_one()
        return self.env.ref(
            'dev_petty_cash.action_report_petty_voucher'
        ).report_action(self)
