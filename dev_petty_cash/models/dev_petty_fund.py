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


class DevPettyFund(models.Model):
    """
    Petty Cash Fund - represents a physical petty cash fund with a designated
    responsible person, cash journal, and replenishment settings.
    """
    _name = 'dev.petty.fund'
    _description = 'Petty Cash Fund'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'name'

    # ------------------
    # Database Indexes
    # ------------------
    # Index on state for filtering active/blocked funds
    # Index on company_id for multi-company queries

    name = fields.Char(
        string='Fund Name',
        required=True,
        tracking=True,
        index=True,
        help='Name of the petty cash fund (e.g., "Office Petty Cash", "Branch A Fund")'
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.company,
        index=True,
        tracking=True,
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        required=True,
        default=lambda self: self.env.company.currency_id,
        tracking=True,
    )
    journal_id = fields.Many2one(
        'account.journal',
        string='Petty Cash Journal',
        required=True,
        domain="[('type', '=', 'cash'), ('company_id', '=', company_id)]",
        tracking=True,
        help='Cash journal used for this petty cash fund. Must be of type Cash.'
    )
    float_amount = fields.Monetary(
        string='Fund Float Amount',
        currency_field='currency_id',
        required=True,
        tracking=True,
        help='The maximum/target amount for this petty cash fund (the float).'
    )
    available_balance = fields.Monetary(
        string='Available Balance',
        currency_field='currency_id',
        compute='_compute_available_balance',
        store=True,
        help='Current available balance = Float Amount - Unpaid Vouchers + Completed Replenishments'
    )
    responsible_user_id = fields.Many2one(
        'res.users',
        string='Responsible Person',
        required=True,
        tracking=True,
        help='User responsible for managing this petty cash fund (custodian).'
    )
    replenish_threshold = fields.Monetary(
        string='Replenishment Threshold',
        currency_field='currency_id',
        tracking=True,
        help='When balance falls below this amount, replenishment will be triggered.'
    )
    replenish_journal_id = fields.Many2one(
        'account.journal',
        string='Replenishment Journal',
        domain="[('type', 'in', ['bank', 'cash']), ('company_id', '=', company_id)]",
        tracking=True,
        help='Bank/Cash journal from which replenishment funds will be sourced.'
    )
    replenish_account_id = fields.Many2one(
        'account.account',
        string='Replenishment Account',
        check_company=True,
        tracking=True,
        help='Account to credit when replenishing (typically bank account).'
    )
    variance_account_id = fields.Many2one(
        'account.account',
        string='Variance Account',
        check_company=True,
        tracking=True,
        help='Account for posting cash shortages/overages during reconciliation.'
    )
    state = fields.Selection([
        ('active', 'Active'),
        ('blocked', 'Blocked'),
    ], string='Status', default='active', required=True, tracking=True, index=True)

    # Related fields for quick access
    voucher_ids = fields.One2many(
        'dev.petty.voucher',
        'fund_id',
        string='Vouchers',
    )
    voucher_count = fields.Integer(
        string='Voucher Count',
        compute='_compute_voucher_count',
    )
    replenish_ids = fields.One2many(
        'dev.petty.replenish',
        'fund_id',
        string='Replenishments',
    )
    pending_voucher_count = fields.Integer(
        string='Pending Vouchers',
        compute='_compute_voucher_count',
    )

    active = fields.Boolean(default=True)
    is_below_threshold = fields.Boolean(
        string='Is Below Threshold',
        compute='_compute_is_below_threshold',
        store=True,
        help='Technical field to filter funds below replenishment threshold'
    )

    # ------------------
    # SQL Constraints
    # ------------------
    _sql_constraints = [
        ('float_amount_positive', 'CHECK(float_amount > 0)',
         'Fund float amount must be greater than zero.'),
        ('replenish_threshold_positive', 'CHECK(replenish_threshold >= 0)',
         'Replenishment threshold must be non-negative.'),
        ('name_company_unique', 'UNIQUE(name, company_id)',
         'Fund name must be unique per company.'),
    ]

    # ------------------
    # Compute Methods
    # ------------------
    @api.depends('float_amount', 'voucher_ids.state', 'voucher_ids.amount',
                 'replenish_ids.state', 'replenish_ids.requested_amount')
    def _compute_available_balance(self):
        """
        Compute the available balance for each fund.

        Formula: Float Amount - Sum(Paid Vouchers not yet reconciled) + Sum(Completed Replenishments)

        Uses efficient SQL query to avoid loading all voucher records.
        """
        self.env['dev.petty.voucher'].flush_model(['state', 'amount', 'fund_id'])
        self.env['dev.petty.replenish'].flush_model(['state', 'requested_amount', 'fund_id', 'update_float'])
        for fund in self:
            # Handle NewId / Virtual Record during Onchange
            # If fund has an origin (real record), use that ID.
            # If it's a completely new record (Start of Create), ID is falsy/NewId without origin.
            real_id = fund.id
            if not isinstance(real_id, int):
                if getattr(fund, '_origin', False):
                    real_id = fund._origin.id
                else:
                    real_id = False

            if not real_id:
                # Truly new record, no history
                fund.available_balance = fund.float_amount
                continue

            # Using SQL for performance on large datasets
            # Sum of paid vouchers (money that has left the fund)
            self.env.cr.execute("""
                    SELECT COALESCE(SUM(amount), 0)
                    FROM dev_petty_voucher
                    WHERE fund_id = %s
                    AND state IN ('paid', 'approved', 'reconciled')
                """, (real_id,))
            paid_vouchers_amount = self.env.cr.fetchone()[0] or 0.0

            # Sum of completed replenishments (money that came into the fund)
            # Subtract any portion that was used to increase the float (as it's already in float_amount)
            self.env.cr.execute("""
                    SELECT COALESCE(SUM(requested_amount) - SUM(COALESCE(float_increase_amount, 0)), 0)
                    FROM dev_petty_replenish
                    WHERE fund_id = %s
                    AND state = 'done'
                """, (real_id,))
            replenish_amount = self.env.cr.fetchone()[0] or 0.0

            # Available = Float - Paid Vouchers + Replenishments (Net of Float Increase)
            fund.available_balance = fund.float_amount - paid_vouchers_amount + replenish_amount
            print('\n\n fund.available_balance>>>>>>>>>>>>>', fund.available_balance)

            
    def _compute_voucher_count(self):
        """Compute total and pending voucher counts."""
        for fund in self:
            fund.voucher_count = len(fund.voucher_ids)
            fund.pending_voucher_count = len(fund.voucher_ids.filtered(
                lambda v: v.state in ('requested', 'approved')
            ))

    @api.depends('available_balance', 'replenish_threshold')
    def _compute_is_below_threshold(self):
        """Flag funds requiring replenishment."""
        for fund in self:
            fund.is_below_threshold = (
                fund.replenish_threshold > 0 and
                fund.available_balance <= fund.replenish_threshold
            )

    # ------------------
    # Onchange Methods
    # ------------------
    # @api.constrains('replenish_account_id', 'variance_account_id', 'company_id')
    # def _check_account_company(self):
    #     """Ensure account belongs to the same company."""
    #     for fund in self:
    #         if fund.replenish_account_id and fund.company_id not in fund.replenish_account_id.company_ids:
    #             raise ValidationError(
    #                 _('The replenishment account "%s" belongs to a different company than the fund.') %
    #                 fund.replenish_account_id.display_name
    #             )
    #         if fund.variance_account_id and fund.company_id not in fund.variance_account_id.company_ids:
    #             raise ValidationError(
    #                 _('The variance account "%s" belongs to a different company than the fund.') %
    #                 fund.variance_account_id.display_name
    #             )

    @api.onchange('company_id')
    def _onchange_company_id(self):
        """Reset journal when company changes."""
        if self.company_id:
            self.currency_id = self.company_id.currency_id
            self.journal_id = False
            self.replenish_journal_id = False
            self.replenish_account_id = False
            self.variance_account_id = False

    @api.onchange('journal_id')
    def _onchange_journal_id(self):
        """Sync currency with journal if set."""
        if self.journal_id and self.journal_id.currency_id:
            self.currency_id = self.journal_id.currency_id

    # ------------------
    # Action Methods
    # ------------------
    def action_block(self):
        """Block the fund - no new vouchers can be created."""
        self.ensure_one()
        if self.state == 'blocked':
            raise UserError(_('Fund is already blocked.'))
        self.write({'state': 'blocked'})
        self.message_post(body=_('Fund has been blocked. No new vouchers can be created.'))
        return True

    def action_unblock(self):
        """Unblock the fund - vouchers can be created again."""
        self.ensure_one()
        if self.state == 'active':
            raise UserError(_('Fund is already active.'))
        self.write({'state': 'active'})
        self.message_post(body=_('Fund has been unblocked and is now active.'))
        return True

    def action_request_replenish(self):
        """
        Create a replenishment request for this fund.
        Opens a wizard to specify the replenishment amount.
        """
        self.ensure_one()
        if not self.replenish_journal_id:
            raise UserError(_('Please configure a replenishment journal for this fund.'))
        if not self.replenish_account_id:
            raise UserError(_('Please configure a replenishment account for this fund.'))

        # Calculate suggested replenishment amount (to bring back to float)
        suggested_amount = self.float_amount - self.available_balance

        return {
            'name': _('Request Replenishment'),
            'type': 'ir.actions.act_window',
            'res_model': 'dev.petty.replenish',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_fund_id': self.id,
                'default_requested_amount': max(suggested_amount, 0),
                'default_requested_by': self.env.user.id,
            },
        }

    def action_view_vouchers(self):
        """Open vouchers view for this fund."""
        self.ensure_one()
        return {
            'name': _('Vouchers'),
            'type': 'ir.actions.act_window',
            'res_model': 'dev.petty.voucher',
            'view_mode': 'list,form',
            'domain': [('fund_id', '=', self.id)],
            'context': {'default_fund_id': self.id},
        }

    def action_view_replenishments(self):
        """Open replenishments view for this fund."""
        self.ensure_one()
        return {
            'name': _('Replenishments'),
            'type': 'ir.actions.act_window',
            'res_model': 'dev.petty.replenish',
            'view_mode': 'list,form',
            'domain': [('fund_id', '=', self.id)],
            'context': {'default_fund_id': self.id},
        }

    # ------------------
    # Cron Methods
    # ------------------
    @api.model
    def _cron_check_replenishment_threshold(self):
        """
        Scheduled action to check all funds and create replenishment requests
        or send notifications when balance falls below threshold.

        This is called by the scheduled cron job.
        """
        funds_below_threshold = self.search([
            ('state', '=', 'active'),
            ('is_below_threshold', '=', True),
        ])

        for fund in funds_below_threshold:
            # Check if there's already a pending replenishment request
            pending_replenish = self.env['dev.petty.replenish'].search([
                ('fund_id', '=', fund.id),
                ('state', 'in', ('draft', 'requested')),
            ], limit=1)

            if not pending_replenish:
                # Create automatic replenishment request
                suggested_amount = fund.float_amount - fund.available_balance
                replenish = self.env['dev.petty.replenish'].create({
                    'fund_id': fund.id,
                    'requested_amount': suggested_amount,
                    'requested_by': fund.responsible_user_id.id,
                    'method': 'auto',
                })

                # Send notification email
                template = self.env.ref(
                    'dev_petty_cash.email_template_replenish_requested',
                    raise_if_not_found=False
                )
                if template:
                    template.send_mail(replenish.id, force_send=True)

                fund.message_post(
                    body=_('Automatic replenishment request created for %s. '
                           'Current balance: %s, Threshold: %s') % (
                        fund.currency_id.symbol + str(suggested_amount),
                        fund.currency_id.symbol + str(fund.available_balance),
                        fund.currency_id.symbol + str(fund.replenish_threshold),
                    ),
                    message_type='notification',
                )

        return True

    @api.model
    def _cron_alert_unreconciled_vouchers(self):
        """
        Scheduled action to alert accounting team about:
        - Funds below threshold
        - Vouchers unreconciled for more than N days (default: 7 days)

        This sends internal notifications and optionally emails.
        """
        # Configuration: days threshold for unreconciled voucher alerts
        UNRECONCILED_DAYS_THRESHOLD = 7

        # Find all companies with petty cash activity
        companies = self.env['res.company'].search([])

        for company in companies:
            alerts = []

            # 1. Check funds below threshold
            critical_funds = self.with_company(company).search([
                ('company_id', '=', company.id),
                ('state', '=', 'active'),
                ('is_below_threshold', '=', True),
            ])

            if critical_funds:
                fund_names = ', '.join(critical_funds.mapped('name'))
                alerts.append(
                    _('Critical Funds (%d): %s') % (len(critical_funds), fund_names)
                )

            # 2. Check for old unreconciled vouchers (using SQL for performance)
            self.env.cr.execute("""
                SELECT v.id, v.name, v.fund_id,
                       (CURRENT_DATE - v.paid_date::date) as days_old
                FROM dev_petty_voucher v
                WHERE v.company_id = %s
                    AND v.state = 'paid'
                    AND v.paid_date < CURRENT_DATE - INTERVAL '%s days'
                ORDER BY v.paid_date
            """, (company.id, UNRECONCILED_DAYS_THRESHOLD))

            old_vouchers = self.env.cr.fetchall()

            if old_vouchers:
                voucher_info = ', '.join([
                    '%s (%d days)' % (v[1], int(v[3])) for v in old_vouchers[:5]
                ])
                if len(old_vouchers) > 5:
                    voucher_info += _(' and %d more...') % (len(old_vouchers) - 5)

                alerts.append(
                    _('Unreconciled Vouchers > %d days (%d): %s') % (
                        UNRECONCILED_DAYS_THRESHOLD,
                        len(old_vouchers),
                        voucher_info
                    )
                )

            # 3. Send notification if there are alerts
            if alerts:
                # Get users to notify (petty cash managers and account managers)
                manager_group = self.env.ref(
                    'dev_petty_cash.group_petty_manager',
                    raise_if_not_found=False
                )
                account_manager_group = self.env.ref(
                    'account.group_account_manager',
                    raise_if_not_found=False
                )

                users_to_notify = self.env['res.users']
                if manager_group:
                    users_to_notify |= manager_group.users
                if account_manager_group:
                    users_to_notify |= account_manager_group.users

                # Filter to company users
                users_to_notify = users_to_notify.filtered(
                    lambda u: company in u.company_ids
                )

                # Create activity for each user
                alert_message = _('Petty Cash Alerts for %s:\n\n%s') % (
                    company.name,
                    '\n'.join('• ' + alert for alert in alerts)
                )

                for user in users_to_notify:
                    self.env['mail.activity'].create({
                        'activity_type_id': self.env.ref('mail.mail_activity_data_todo').id,
                        'note': alert_message,
                        'user_id': user.id,
                        'res_model_id': self.env['ir.model']._get('dev.petty.fund').id,
                        'res_id': critical_funds[0].id if critical_funds else False,
                        'summary': _('Petty Cash Alert'),
                    })

        return True

    @api.model
    def _cron_send_dashboard_summary(self):
        """
        Scheduled action to send weekly dashboard summary email.

        This creates a summary of petty cash status across all funds
        and sends it to configured recipients.
        """
        companies = self.env['res.company'].search([])

        for company in companies:
            # Get dashboard KPI data
            kpi = self.env['dev.petty.dashboard.kpi'].search([
                ('company_id', '=', company.id)
            ], limit=1)

            if not kpi:
                continue

            # Get critical/warning funds
            fund_dashboard = self.env['dev.petty.dashboard.fund'].search([
                ('company_id', '=', company.id),
                ('status', 'in', ['critical', 'warning']),
            ])

            # Build summary
            summary_lines = [
                _('<h2>Petty Cash Weekly Summary - %s</h2>') % company.name,
                _('<p><strong>Date:</strong> %s</p>') % fields.Date.today(),
                '',
                _('<h3>Overview</h3>'),
                _('<ul>'),
                _('<li>Total Float: %s %s</li>') % (kpi.currency_id.symbol, kpi.total_float_amount),
                _('<li>Available Balance: %s %s</li>') % (kpi.currency_id.symbol, kpi.total_available_balance),
                _('<li>Current Month Spend: %s %s</li>') % (kpi.currency_id.symbol, kpi.current_month_spend),
                _('<li>Funds Below Threshold: %d</li>') % kpi.funds_below_threshold,
                _('<li>Pending Approval: %d vouchers (%s %s)</li>') % (
                    kpi.pending_approval_count,
                    kpi.currency_id.symbol,
                    kpi.pending_approval_amount
                ),
                _('<li>Unreconciled: %d vouchers (%s %s)</li>') % (
                    kpi.unreconciled_count,
                    kpi.currency_id.symbol,
                    kpi.unreconciled_amount
                ),
                _('</ul>'),
            ]

            if fund_dashboard:
                summary_lines.extend([
                    '',
                    _('<h3>Funds Requiring Attention</h3>'),
                    _('<table border="1" cellpadding="5">'),
                    _('<tr><th>Fund</th><th>Status</th><th>Available</th><th>Threshold</th></tr>'),
                ])
                for fund in fund_dashboard:
                    status_color = 'red' if fund.status == 'critical' else 'orange'
                    summary_lines.append(
                        _('<tr><td>%s</td><td style="color:%s">%s</td><td>%s %s</td><td>%s %s</td></tr>') % (
                            fund.name,
                            status_color,
                            fund.status.upper(),
                            fund.currency_id.symbol,
                            fund.available_balance,
                            fund.currency_id.symbol,
                            fund.replenish_threshold,
                        )
                    )
                summary_lines.append(_('</table>'))

            summary_html = '\n'.join(summary_lines)

            # Get recipients
            manager_group = self.env.ref(
                'dev_petty_cash.group_petty_manager',
                raise_if_not_found=False
            )
            recipients = []
            if manager_group:
                recipients = manager_group.users.filtered(
                    lambda u: company in u.company_ids and u.email
                ).mapped('email')

            if recipients:
                # Send email
                mail_values = {
                    'subject': _('Petty Cash Weekly Summary - %s') % company.name,
                    'body_html': summary_html,
                    'email_to': ','.join(recipients),
                    'auto_delete': True,
                }
                self.env['mail.mail'].create(mail_values).send()

        return True

    # ------------------
    # Name Methods
    # ------------------
    def name_get(self):
        result = []
        for fund in self:
            name = '%s (%s)' % (fund.name, fund.currency_id.symbol + str(fund.available_balance))
            result.append((fund.id, name))
        return result
