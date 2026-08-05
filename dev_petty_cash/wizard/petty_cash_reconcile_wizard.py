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


class PettyCashReconcileWizard(models.TransientModel):
    """
    Wizard for reconciling petty cash vouchers.
    Allows uploading receipts and creating variance entries.
    """
    _name = 'petty.cash.reconcile.wizard'
    _description = 'Petty Cash Reconciliation Wizard'

    voucher_id = fields.Many2one(
        'dev.petty.voucher',
        string='Voucher',
        required=True,
        readonly=True,
    )
    fund_id = fields.Many2one(
        'dev.petty.fund',
        string='Fund',
        related='voucher_id.fund_id',
        readonly=True,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        related='voucher_id.company_id',
        readonly=True,
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        related='voucher_id.currency_id',
        readonly=True,
    )
    paid_amount = fields.Monetary(
        string='Amount Paid',
        currency_field='currency_id',
        readonly=True,
        help='The amount that was paid out from petty cash.',
    )
    receipt_total = fields.Monetary(
        string='Receipt Total',
        currency_field='currency_id',
        required=True,
        help='Total amount from the receipts/invoices attached.',
    )
    variance_amount = fields.Monetary(
        string='Variance',
        currency_field='currency_id',
        compute='_compute_variance',
        help='Difference between paid amount and receipt total. Positive = overage, Negative = shortage.',
    )
    variance_type = fields.Selection([
        ('none', 'No Variance'),
        ('shortage', 'Cash Shortage'),
        ('overage', 'Cash Overage'),
    ], string='Variance Type', compute='_compute_variance')
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'petty_reconcile_wizard_attachment_rel',
        'wizard_id',
        'attachment_id',
        string='Receipt Attachments',
        help='Upload receipt images/PDFs for reconciliation.',
    )
    notes = fields.Text(
        string='Notes',
        help='Additional notes about the reconciliation.',
    )
    create_variance_entry = fields.Boolean(
        string='Create Variance Entry',
        default=True,
        help='Automatically create a journal entry for the variance.',
    )

    # ------------------
    # Compute Methods
    # ------------------
    @api.depends('paid_amount', 'receipt_total')
    def _compute_variance(self):
        """Compute variance amount and type."""
        for wizard in self:
            wizard.variance_amount = wizard.paid_amount - wizard.receipt_total
            if wizard.variance_amount > 0:
                wizard.variance_type = 'overage'
            elif wizard.variance_amount < 0:
                wizard.variance_type = 'shortage'
            else:
                wizard.variance_type = 'none'

    # ------------------
    # Action Methods
    # ------------------
    def action_reconcile(self):
        """
        Process the reconciliation:
        1. Attach receipts to voucher
        2. Create variance journal entry if needed
        3. Mark voucher as reconciled
        """
        self.ensure_one()

        if self.receipt_total <= 0:
            raise ValidationError(_('Receipt total must be greater than zero.'))

        voucher = self.voucher_id
        fund = self.fund_id

        # Attach receipts to voucher
        if self.attachment_ids:
            voucher.write({
                'attachment_ids': [(4, att.id) for att in self.attachment_ids]
            })

        # Create variance entry if needed
        variance_move = None
        if self.variance_amount != 0 and self.create_variance_entry:
            variance_move = self._create_variance_move()

        # Mark voucher as reconciled
        voucher.action_mark_reconciled(
            receipt_total=self.receipt_total,
            variance_move=variance_move,
        )

        # Log notes if provided
        if self.notes:
            voucher.message_post(
                body=_('Reconciliation notes: %s') % self.notes
            )

        return {
            'type': 'ir.actions.act_window_close',
        }

    def _create_variance_move(self):
        """
        Create a journal entry for the variance.

        Shortage (paid more than receipts):
        - Debit: Variance Account (loss)
        - Credit: Petty Cash Account

        Overage (receipts more than paid - unlikely but handled):
        - Debit: Petty Cash Account
        - Credit: Variance Account (gain)
        """
        self.ensure_one()

        fund = self.fund_id
        voucher = self.voucher_id

        # Get variance account
        variance_account = fund.variance_account_id
        if not variance_account:
            raise UserError(
                _('Please configure a variance account on the fund "%s" '
                  'before creating variance entries.') % fund.name
            )

        # Get petty cash account from journal
        petty_cash_journal = fund.journal_id
        petty_cash_account = (
            petty_cash_journal.default_account_id or
            petty_cash_journal.company_id.account_journal_payment_credit_account_id
        )
        if not petty_cash_account:
            raise UserError(
                _('Please configure a default account on the petty cash journal.')
            )

        variance_abs = abs(self.variance_amount)

        if self.variance_type == 'overage':
            # Overage: received more in receipts than paid out (unusual)
            # This means we have extra cash, so credit variance (income)
            lines = [
                (0, 0, {
                    'name': _('Cash Overage - %s') % voucher.name,
                    'account_id': petty_cash_account.id,
                    'debit': variance_abs,
                    'credit': 0.0,
                }),
                (0, 0, {
                    'name': _('Cash Overage - %s') % voucher.name,
                    'account_id': variance_account.id,
                    'debit': 0.0,
                    'credit': variance_abs,
                }),
            ]
        else:
            # Shortage: paid out more than receipts show (common)
            # This means cash is missing, so debit variance (expense)
            lines = [
                (0, 0, {
                    'name': _('Cash Shortage - %s') % voucher.name,
                    'account_id': variance_account.id,
                    'debit': variance_abs,
                    'credit': 0.0,
                }),
                (0, 0, {
                    'name': _('Cash Shortage - %s') % voucher.name,
                    'account_id': petty_cash_account.id,
                    'debit': 0.0,
                    'credit': variance_abs,
                }),
            ]

        move_vals = {
            'move_type': 'entry',
            'journal_id': petty_cash_journal.id,
            'date': fields.Date.context_today(self),
            'ref': _('Variance Adjustment - %s') % voucher.name,
            'company_id': self.company_id.id,
            'line_ids': lines,
        }

        # Create and post the move
        move = self.env['account.move'].with_company(self.company_id).create(move_vals)
        move.action_post()

        return move

    def action_cancel(self):
        """Cancel and close the wizard."""
        return {'type': 'ir.actions.act_window_close'}
