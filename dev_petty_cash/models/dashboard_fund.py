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
Dashboard Fund Monitoring Model - SQL View Based

This model provides per-fund metrics for the dashboard fund monitoring table.
It uses a PostgreSQL view for high-performance aggregations.

Status Logic:
- Critical: available_balance <= replenish_threshold
- Warning: available_balance < 30% of float_amount
- OK: otherwise
"""

from odoo import api, fields, models, tools


class DevPettyDashboardFund(models.Model):
    """
    SQL View model for Fund Monitoring Dashboard.

    Provides per-fund metrics including:
    - Float amount and available balance
    - Utilization percentage
    - Status indicator (OK/Warning/Critical)
    - Last replenishment date
    - Voucher statistics per fund
    """
    _name = 'dev.petty.dashboard.fund'
    _description = 'Petty Cash Fund Dashboard'
    _auto = False  # SQL View - no automatic table creation
    _order = 'status_priority desc, name'

    # Fund identification
    name = fields.Char(
        string='Fund Name',
        readonly=True,
    )
    fund_id = fields.Many2one(
        'dev.petty.fund',
        string='Fund',
        readonly=True,
    )
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
    responsible_user_id = fields.Many2one(
        'res.users',
        string='Cashier',
        readonly=True,
    )
    journal_id = fields.Many2one(
        'account.journal',
        string='Journal',
        readonly=True,
    )

    # Fund amounts
    float_amount = fields.Monetary(
        string='Float Amount',
        currency_field='currency_id',
        readonly=True,
    )
    available_balance = fields.Monetary(
        string='Available Balance',
        currency_field='currency_id',
        readonly=True,
    )
    replenish_threshold = fields.Monetary(
        string='Threshold',
        currency_field='currency_id',
        readonly=True,
    )

    # Computed metrics
    utilization_percentage = fields.Float(
        string='Utilization %',
        readonly=True,
        help='Percentage of float that has been utilized: ((float - available) / float) * 100',
    )
    balance_percentage = fields.Float(
        string='Balance %',
        readonly=True,
        help='Percentage of float available: (available / float) * 100',
    )

    # Status
    status = fields.Selection([
        ('ok', 'OK'),
        ('warning', 'Warning'),
        ('critical', 'Critical'),
    ], string='Status', readonly=True)
    status_priority = fields.Integer(
        string='Status Priority',
        readonly=True,
        help='For sorting: Critical=3, Warning=2, OK=1',
    )
    fund_state = fields.Selection([
        ('active', 'Active'),
        ('blocked', 'Blocked'),
    ], string='Fund State', readonly=True)

    # Dates
    last_replenishment_date = fields.Date(
        string='Last Replenishment',
        readonly=True,
    )
    last_voucher_date = fields.Date(
        string='Last Voucher',
        readonly=True,
    )

    # Voucher statistics
    pending_vouchers_count = fields.Integer(
        string='Pending Vouchers',
        readonly=True,
        help='Number of vouchers awaiting approval for this fund.',
    )
    pending_vouchers_amount = fields.Monetary(
        string='Pending Amount',
        currency_field='currency_id',
        readonly=True,
    )
    unreconciled_vouchers_count = fields.Integer(
        string='Unreconciled',
        readonly=True,
        help='Number of paid vouchers not yet reconciled.',
    )
    month_vouchers_count = fields.Integer(
        string='Monthly Vouchers',
        readonly=True,
        help='Number of vouchers this month.',
    )
    month_spend = fields.Monetary(
        string='Monthly Spend',
        currency_field='currency_id',
        readonly=True,
    )

    def init(self):
        """
        Create the SQL view for fund monitoring dashboard.

        This view provides per-fund metrics with status calculation.
        All calculations are done in SQL for performance.
        """
        tools.drop_view_if_exists(self.env.cr, self._table)

        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    f.id AS id,
                    f.id AS fund_id,
                    f.name AS name,
                    f.company_id AS company_id,
                    f.currency_id AS currency_id,
                    f.responsible_user_id AS responsible_user_id,
                    f.journal_id AS journal_id,
                    f.float_amount AS float_amount,
                    f.available_balance AS available_balance,
                    f.replenish_threshold AS replenish_threshold,
                    f.state AS fund_state,

                    -- Utilization percentage: ((float - available) / float) * 100
                    CASE
                        WHEN f.float_amount > 0
                        THEN ROUND(((f.float_amount - f.available_balance) / f.float_amount * 100)::numeric, 1)
                        ELSE 0
                    END AS utilization_percentage,

                    -- Balance percentage: (available / float) * 100
                    CASE
                        WHEN f.float_amount > 0
                        THEN ROUND((f.available_balance / f.float_amount * 100)::numeric, 1)
                        ELSE 0
                    END AS balance_percentage,

                    -- Status calculation
                    CASE
                        WHEN f.replenish_threshold > 0
                            AND f.available_balance <= COALESCE(f.replenish_threshold, 0)
                        THEN 'critical'
                        WHEN f.float_amount > 0
                            AND f.available_balance < (f.float_amount * 0.3)
                        THEN 'warning'
                        ELSE 'ok'
                    END AS status,

                    -- Status priority for sorting (critical first)
                    CASE
                        WHEN f.replenish_threshold > 0
                            AND f.available_balance <= COALESCE(f.replenish_threshold, 0)
                        THEN 3
                        WHEN f.float_amount > 0
                            AND f.available_balance < (f.float_amount * 0.3)
                        THEN 2
                        ELSE 1
                    END AS status_priority,

                    -- Last replenishment date
                    (
                        SELECT MAX(r.requested_date)::date
                        FROM dev_petty_replenish r
                        WHERE r.fund_id = f.id AND r.state = 'done'
                    ) AS last_replenishment_date,

                    -- Last voucher date
                    (
                        SELECT MAX(v.date)
                        FROM dev_petty_voucher v
                        WHERE v.fund_id = f.id AND v.state NOT IN ('draft', 'cancelled')
                    ) AS last_voucher_date,

                    -- Pending vouchers
                    COALESCE(vs.pending_vouchers_count, 0) AS pending_vouchers_count,
                    COALESCE(vs.pending_vouchers_amount, 0) AS pending_vouchers_amount,
                    COALESCE(vs.unreconciled_vouchers_count, 0) AS unreconciled_vouchers_count,
                    COALESCE(vs.month_vouchers_count, 0) AS month_vouchers_count,
                    COALESCE(vs.month_spend, 0) AS month_spend

                FROM dev_petty_fund f

                -- Voucher statistics per fund
                LEFT JOIN (
                    SELECT
                        v.fund_id,
                        SUM(CASE WHEN v.state = 'requested' THEN 1 ELSE 0 END) AS pending_vouchers_count,
                        SUM(CASE WHEN v.state = 'requested' THEN v.amount ELSE 0 END) AS pending_vouchers_amount,
                        SUM(CASE WHEN v.state = 'paid' THEN 1 ELSE 0 END) AS unreconciled_vouchers_count,
                        SUM(CASE
                            WHEN v.state IN ('paid', 'reconciled')
                                AND v.date >= DATE_TRUNC('month', CURRENT_DATE)
                            THEN 1 ELSE 0
                        END) AS month_vouchers_count,
                        SUM(CASE
                            WHEN v.state IN ('paid', 'reconciled')
                                AND v.date >= DATE_TRUNC('month', CURRENT_DATE)
                            THEN v.amount ELSE 0
                        END) AS month_spend
                    FROM dev_petty_voucher v
                    WHERE v.state != 'cancelled'
                    GROUP BY v.fund_id
                ) vs ON vs.fund_id = f.id

                WHERE f.active = TRUE
            )
        """ % (self._table,))

    # ------------------
    # Action Methods
    # ------------------
    def action_view_fund(self):
        """Open the fund form view."""
        self.ensure_one()
        return {
            'name': self.name,
            'type': 'ir.actions.act_window',
            'res_model': 'dev.petty.fund',
            'view_mode': 'form',
            'res_id': self.fund_id.id,
        }

    def action_view_fund_vouchers(self):
        """Open vouchers for this fund."""
        self.ensure_one()
        return {
            'name': f'Vouchers - {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'dev.petty.voucher',
            'view_mode': 'list,form',
            'domain': [('fund_id', '=', self.fund_id.id)],
            'context': {'default_fund_id': self.fund_id.id},
        }

    def action_view_pending_vouchers(self):
        """Open pending vouchers for this fund."""
        self.ensure_one()
        return {
            'name': f'Pending Vouchers - {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'dev.petty.voucher',
            'view_mode': 'list,form',
            'domain': [
                ('fund_id', '=', self.fund_id.id),
                ('state', '=', 'requested'),
            ],
        }

    def action_request_replenishment(self):
        """Open replenishment request wizard for this fund."""
        self.ensure_one()
        fund = self.fund_id
        suggested_amount = fund.float_amount - fund.available_balance

        return {
            'name': 'Request Replenishment',
            'type': 'ir.actions.act_window',
            'res_model': 'dev.petty.replenish',
            'view_mode': 'form',
            'target': 'new',
            'context': {
                'default_fund_id': fund.id,
                'default_requested_amount': max(suggested_amount, 0),
            },
        }

    def action_view_replenishments(self):
        """Open replenishments for this fund."""
        self.ensure_one()
        return {
            'name': f'Replenishments - {self.name}',
            'type': 'ir.actions.act_window',
            'res_model': 'dev.petty.replenish',
            'view_mode': 'list,form',
            'domain': [('fund_id', '=', self.fund_id.id)],
        }
