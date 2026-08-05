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
Dashboard KPI Model - SQL View Based

This model provides aggregated KPIs for the petty cash dashboard.
It uses a PostgreSQL view for high-performance aggregations without ORM loops.

The view is multi-company safe and filters by company_id.
All aggregations are done in SQL for optimal performance.
"""

from odoo import api, fields, models, tools, _


class DevPettyDashboardKpi(models.Model):
    """
    SQL View model for Petty Cash Dashboard KPIs.

    Provides company-aware aggregated metrics:
    - Total float amount across all funds
    - Total available balance
    - Pending approval amounts
    - Unreconciled voucher amounts
    - Funds below threshold count
    - Current month spend
    """
    _name = 'dev.petty.dashboard.kpi'
    _description = 'Petty Cash Dashboard KPIs'
    _auto = False  # SQL View - no automatic table creation
    _order = 'company_id'
    _log_access = False

    @api.model_create_multi
    def create(self, vals_list):
        """
        Mock create to handle UI 'save' actions on this SQL view.
        Since the ID in the view is the company_id, we simply return
        the record for the current company.
        """
        return self.browse([self.env.company.id for _ in vals_list])

    def write(self, vals):
        """Mock write to handle UI 'save' actions."""
        return True

    def unlink(self):
        """Prevent deletion."""
        return True

    today_date = fields.Date(string='Today', compute='_compute_today_date')
    name = fields.Char(string='Name', compute='_compute_name')

    def _compute_today_date(self):
        for record in self:
            record.today_date = fields.Date.context_today(record)

    def _compute_name(self):
        for record in self:
            record.name = _("Petty Cash Dashboard")

    def _compute_display_name(self):
        for record in self:
            record.display_name = _("Petty Cash Dashboard")

    # Company field for multi-company filtering
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        readonly=True,
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        readonly=True,
    )

    # Fund KPIs
    total_float_amount = fields.Monetary(
        string='Total Petty Cash Float',
        currency_field='currency_id',
        readonly=True,
        help='Sum of float amounts across all active petty cash funds.',
    )
    total_available_balance = fields.Monetary(
        string='Total Available Balance',
        currency_field='currency_id',
        readonly=True,
        help='Sum of available balances across all active funds.',
    )
    funds_count = fields.Integer(
        string='Total Funds',
        readonly=True,
        help='Total number of active petty cash funds.',
    )
    funds_below_threshold = fields.Integer(
        string='Funds Below Threshold',
        readonly=True,
        help='Number of funds with available balance at or below replenishment threshold.',
    )
    funds_critical_count = fields.Integer(
        string='Critical Funds',
        readonly=True,
        help='Number of funds in critical status (balance <= threshold).',
    )
    funds_warning_count = fields.Integer(
        string='Warning Funds',
        readonly=True,
        help='Number of funds in warning status (balance < 30% of float).',
    )

    # Voucher KPIs
    pending_approval_amount = fields.Monetary(
        string='Pending Approval Amount',
        currency_field='currency_id',
        readonly=True,
        help='Total amount of vouchers awaiting approval.',
    )
    pending_approval_count = fields.Integer(
        string='Pending Approval Count',
        readonly=True,
        help='Number of vouchers awaiting approval.',
    )
    unreconciled_amount = fields.Monetary(
        string='Unreconciled Amount',
        currency_field='currency_id',
        readonly=True,
        help='Total amount of paid vouchers not yet reconciled.',
    )
    unreconciled_count = fields.Integer(
        string='Unreconciled Count',
        readonly=True,
        help='Number of paid vouchers not yet reconciled.',
    )
    current_month_spend = fields.Monetary(
        string='Current Month Spend',
        currency_field='currency_id',
        readonly=True,
        help='Total petty cash spent in the current month.',
    )

    # Risk Metrics
    total_variance = fields.Monetary(
        string='Total Variance',
        currency_field='currency_id',
        readonly=True,
        help='Sum of all variance amounts (shortages/overages).',
    )
    missing_receipts_count = fields.Integer(
        string='Missing Receipts',
        readonly=True,
        help='Number of paid/reconciled vouchers without attachments.',
    )
    oldest_unreconciled_days = fields.Integer(
        string='Oldest Unreconciled (Days)',
        readonly=True,
        help='Age in days of the oldest unreconciled voucher.',
    )

    # Replenishment KPIs
    pending_replenish_amount = fields.Monetary(
        string='Pending Replenishment Amount',
        currency_field='currency_id',
        readonly=True,
        help='Total amount of pending replenishment requests.',
    )
    pending_replenish_count = fields.Integer(
        string='Pending Replenishment Count',
        readonly=True,
        help='Number of pending replenishment requests.',
    )

    def init(self):
        """
        Create the SQL view for dashboard KPIs.

        This view aggregates data from:
        - dev_petty_fund: Fund totals and threshold status
        - dev_petty_voucher: Voucher amounts by state
        - dev_petty_replenish: Replenishment requests

        All aggregations are done in SQL for performance.
        Uses COALESCE for NULL safety throughout.
        """
        tools.drop_view_if_exists(self.env.cr, self._table)

        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    -- Use company_id as primary key for uniqueness
                    c.id AS id,
                    c.id AS company_id,
                    c.currency_id AS currency_id,

                    -- Fund KPIs
                    COALESCE(fund_stats.total_float_amount, 0) AS total_float_amount,
                    COALESCE(fund_stats.total_available_balance, 0) AS total_available_balance,
                    COALESCE(fund_stats.funds_count, 0) AS funds_count,
                    COALESCE(fund_stats.funds_below_threshold, 0) AS funds_below_threshold,
                    COALESCE(fund_stats.funds_critical_count, 0) AS funds_critical_count,
                    COALESCE(fund_stats.funds_warning_count, 0) AS funds_warning_count,

                    -- Voucher KPIs
                    COALESCE(voucher_stats.pending_approval_amount, 0) AS pending_approval_amount,
                    COALESCE(voucher_stats.pending_approval_count, 0) AS pending_approval_count,
                    COALESCE(voucher_stats.unreconciled_amount, 0) AS unreconciled_amount,
                    COALESCE(voucher_stats.unreconciled_count, 0) AS unreconciled_count,
                    COALESCE(voucher_stats.current_month_spend, 0) AS current_month_spend,
                    COALESCE(voucher_stats.total_variance, 0) AS total_variance,
                    COALESCE(voucher_stats.missing_receipts_count, 0) AS missing_receipts_count,
                    COALESCE(voucher_stats.oldest_unreconciled_days, 0) AS oldest_unreconciled_days,

                    -- Replenishment KPIs
                    COALESCE(replenish_stats.pending_replenish_amount, 0) AS pending_replenish_amount,
                    COALESCE(replenish_stats.pending_replenish_count, 0) AS pending_replenish_count

                FROM res_company c

                -- Fund statistics subquery
                LEFT JOIN (
                    SELECT
                        f.company_id,
                        SUM(f.float_amount) AS total_float_amount,
                        SUM(f.available_balance) AS total_available_balance,
                        COUNT(f.id) AS funds_count,
                        SUM(CASE
                            WHEN f.replenish_threshold > 0
                                AND f.available_balance <= f.replenish_threshold
                            THEN 1 ELSE 0
                        END) AS funds_below_threshold,
                        SUM(CASE
                            WHEN f.replenish_threshold > 0
                                AND f.available_balance <= f.replenish_threshold
                            THEN 1 ELSE 0
                        END) AS funds_critical_count,
                        SUM(CASE
                            WHEN f.available_balance > f.replenish_threshold
                                AND f.available_balance < (f.float_amount * 0.3)
                            THEN 1 ELSE 0
                        END) AS funds_warning_count
                    FROM dev_petty_fund f
                    WHERE f.state = 'active' AND f.active = TRUE
                    GROUP BY f.company_id
                ) fund_stats ON fund_stats.company_id = c.id

                -- Voucher statistics subquery
                LEFT JOIN (
                    SELECT
                        v.company_id,
                        -- Pending approval
                        SUM(CASE WHEN v.state = 'requested' THEN v.amount ELSE 0 END) AS pending_approval_amount,
                        SUM(CASE WHEN v.state = 'requested' THEN 1 ELSE 0 END) AS pending_approval_count,
                        -- Unreconciled
                        SUM(CASE WHEN v.state = 'paid' THEN v.amount ELSE 0 END) AS unreconciled_amount,
                        SUM(CASE WHEN v.state = 'paid' THEN 1 ELSE 0 END) AS unreconciled_count,
                        -- Current month spend (paid + reconciled this month)
                        SUM(CASE
                            WHEN v.state IN ('paid', 'reconciled')
                                AND v.paid_date >= DATE_TRUNC('month', CURRENT_DATE)
                            THEN v.amount ELSE 0
                        END) AS current_month_spend,
                        -- Total variance
                        SUM(CASE
                            WHEN v.state = 'reconciled'
                            THEN ABS(COALESCE(v.variance_amount, 0)) ELSE 0
                        END) AS total_variance,
                        -- Missing receipts (paid/reconciled without attachments)
                        SUM(CASE
                            WHEN v.state IN ('paid', 'reconciled')
                                AND NOT EXISTS (
                                    SELECT 1 FROM dev_petty_voucher_attachment_rel rel
                                    WHERE rel.voucher_id = v.id
                                )
                            THEN 1 ELSE 0
                        END) AS missing_receipts_count,
                        -- Oldest unreconciled voucher age
                        MAX(CASE
                            WHEN v.state = 'paid'
                            THEN (CURRENT_DATE - v.paid_date::date)
                            ELSE 0
                        END) AS oldest_unreconciled_days
                    FROM dev_petty_voucher v
                    WHERE v.state != 'cancelled'
                    GROUP BY v.company_id
                ) voucher_stats ON voucher_stats.company_id = c.id

                -- Replenishment statistics subquery
                LEFT JOIN (
                    SELECT
                        r.company_id,
                        SUM(CASE
                            WHEN r.state IN ('draft', 'requested', 'approved')
                            THEN r.requested_amount ELSE 0
                        END) AS pending_replenish_amount,
                        SUM(CASE
                            WHEN r.state IN ('draft', 'requested', 'approved')
                            THEN 1 ELSE 0
                        END) AS pending_replenish_count
                    FROM dev_petty_replenish r
                    GROUP BY r.company_id
                ) replenish_stats ON replenish_stats.company_id = c.id

                WHERE c.id IS NOT NULL
            )
        """ % (self._table,))

    # ------------------
    # Action Methods
    # ------------------
    def action_view_pending_vouchers(self):
        """Open vouchers pending approval for this company."""
        self.ensure_one()
        return {
            'name': 'Vouchers Pending Approval',
            'type': 'ir.actions.act_window',
            'res_model': 'dev.petty.voucher',
            'view_mode': 'list,form',
            'domain': [
                ('company_id', '=', self.company_id.id),
                ('state', '=', 'requested'),
            ],
            'context': {'search_default_filter_requested': 1},
        }

    def action_view_unreconciled_vouchers(self):
        """Open unreconciled vouchers for this company."""
        self.ensure_one()
        return {
            'name': 'Unreconciled Vouchers',
            'type': 'ir.actions.act_window',
            'res_model': 'dev.petty.voucher',
            'view_mode': 'list,form',
            'domain': [
                ('company_id', '=', self.company_id.id),
                ('state', '=', 'paid'),
            ],
            'context': {'search_default_filter_paid': 1},
        }

    def action_view_critical_funds(self):
        """Open funds in critical status for this company."""
        self.ensure_one()
        return {
            'name': 'Critical Funds',
            'type': 'ir.actions.act_window',
            'res_model': 'dev.petty.fund',
            'view_mode': 'list,form',
            'domain': [
                ('company_id', '=', self.company_id.id),
                ('state', '=', 'active'),
            ],
            'context': {'search_default_filter_below_threshold': 1},
        }

    def action_view_missing_receipts(self):
        """Open vouchers with missing receipts."""
        self.ensure_one()
        # Get voucher IDs without attachments
        self.env.cr.execute("""
            SELECT v.id
            FROM dev_petty_voucher v
            WHERE v.company_id = %s
                AND v.state IN ('paid', 'reconciled')
                AND NOT EXISTS (
                    SELECT 1 FROM dev_petty_voucher_attachment_rel rel
                    WHERE rel.voucher_id = v.id
                )
        """, (self.company_id.id,))
        voucher_ids = [r[0] for r in self.env.cr.fetchall()]

        return {
            'name': 'Vouchers Missing Receipts',
            'type': 'ir.actions.act_window',
            'res_model': 'dev.petty.voucher',
            'view_mode': 'list,form',
            'domain': [('id', 'in', voucher_ids)],
        }

    def action_view_all_funds(self):
        """Open all funds for this company."""
        self.ensure_one()
        return {
            'name': 'Petty Cash Funds',
            'type': 'ir.actions.act_window',
            'res_model': 'dev.petty.fund',
            'view_mode': 'list,kanban,form',
            'domain': [('company_id', '=', self.company_id.id)],
        }

    def action_view_pending_replenishments(self):
        """Open pending replenishment requests."""
        self.ensure_one()
        return {
            'name': 'Pending Replenishments',
            'type': 'ir.actions.act_window',
            'res_model': 'dev.petty.replenish',
            'view_mode': 'list,form',
            'domain': [
                ('company_id', '=', self.company_id.id),
                ('state', 'in', ['draft', 'requested', 'approved']),
            ],
        }

    @api.model
    def action_open_dashboard(self):
        """
        Open the dashboard for the current company.
        This method is called from the menu action to ensure the correct
        company record is loaded and data is refreshed.
        """
        # Get the window action definition from XML
        action = self.env['ir.actions.act_window']._for_xml_id('dev_petty_cash.action_petty_cash_dashboard_window')
        
        # Get or create dashboard record for current company
        company = self.env.company
        dashboard = self.search([('company_id', '=', company.id)], limit=1)

        if dashboard:
            action['res_id'] = dashboard.id
        
        # Override the action ID with the Server Action ID
        # This ensures the browser URL matches the menu item (which points to this server action)
        # preventing the "menu tabs disappear" issue on reload.
        # Also ensures the breadcrumb uses the Server Action name ("Petty Cash Dashboard") instead of "New".
        try:
            server_action = self.env.ref('dev_petty_cash.action_petty_cash_dashboard_kpi')
            action['id'] = server_action.id
        except ValueError:
            pass # Fallback: leave action['id'] as window action ID
            
        return action

    def refresh_dashboard_data(self):
        """
        Force refresh of dashboard data by invalidating the cache and reloading the view.
        Called when user clicks the Refresh button on dashboard.
        """
        self.invalidate_model()
        # Return action to reload the current form view without adding breadcrumbs
        return {
            'type': 'ir.actions.client',
            'tag': 'reload',
        }
