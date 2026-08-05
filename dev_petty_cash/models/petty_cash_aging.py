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
Petty Cash Aging Report

This module implements a SQL VIEW for aging analysis of petty cash vouchers.
It tracks:
- Vouchers awaiting approval (state = requested)
- Paid vouchers awaiting reconciliation (state = paid)

Aging buckets: 0-7 days, 8-15 days, 16-30 days, 30+ days
"""

from odoo import api, fields, models, tools


class DevPettyCashAgingReport(models.Model):
    """
    Petty Cash Aging Report (SQL View).

    Provides aging analysis for pending vouchers with configurable buckets.
    This is a read-only model mapped to a SQL view.
    """
    _name = 'dev.petty.cash.aging.report'
    _description = 'Petty Cash Aging Report'
    _auto = False
    _order = 'days_pending desc'

    # Voucher reference
    voucher_id = fields.Many2one(
        'dev.petty.voucher',
        string='Voucher',
        readonly=True,
    )
    voucher_name = fields.Char(
        string='Voucher Reference',
        readonly=True,
    )
    fund_id = fields.Many2one(
        'dev.petty.fund',
        string='Fund',
        readonly=True,
    )
    fund_name = fields.Char(
        string='Fund Name',
        readonly=True,
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        readonly=True,
    )
    requester_id = fields.Many2one(
        'res.users',
        string='Requester',
        readonly=True,
    )

    # Voucher details
    voucher_date = fields.Date(
        string='Voucher Date',
        readonly=True,
    )
    amount = fields.Monetary(
        string='Amount',
        currency_field='currency_id',
        readonly=True,
    )
    currency_id = fields.Many2one(
        'res.currency',
        string='Currency',
        readonly=True,
    )
    state = fields.Selection([
        ('requested', 'Awaiting Approval'),
        ('paid', 'Awaiting Reconciliation'),
    ], string='Status', readonly=True)
    state_display = fields.Char(
        string='Status Display',
        readonly=True,
    )

    # Aging analysis
    days_pending = fields.Integer(
        string='Days Pending',
        readonly=True,
        help='Number of days since voucher date.',
    )
    aging_bucket = fields.Selection([
        ('0_7_days', '0-7 Days'),
        ('8_15_days', '8-15 Days'),
        ('16_30_days', '16-30 Days'),
        ('above_30_days', '30+ Days'),
    ], string='Aging Bucket', readonly=True)
    aging_bucket_display = fields.Char(
        string='Aging',
        readonly=True,
    )

    # Category
    pending_type = fields.Selection([
        ('approval', 'Pending Approval'),
        ('reconciliation', 'Pending Reconciliation'),
    ], string='Pending Type', readonly=True)

    def init(self):
        """Create or replace the SQL view."""
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    v.id AS id,
                    v.id AS voucher_id,
                    v.name AS voucher_name,
                    v.fund_id AS fund_id,
                    f.name AS fund_name,
                    v.company_id AS company_id,
                    v.requester_id AS requester_id,
                    v.date AS voucher_date,
                    v.amount AS amount,
                    v.currency_id AS currency_id,
                    v.state AS state,
                    CASE
                        WHEN v.state = 'requested' THEN 'Awaiting Approval'
                        WHEN v.state = 'paid' THEN 'Awaiting Reconciliation'
                    END AS state_display,
                    -- Calculate days pending
                    (CURRENT_DATE - v.date)::INTEGER AS days_pending,
                    -- Aging bucket
                    CASE
                        WHEN (CURRENT_DATE - v.date) <= 7 THEN '0_7_days'
                        WHEN (CURRENT_DATE - v.date) <= 15 THEN '8_15_days'
                        WHEN (CURRENT_DATE - v.date) <= 30 THEN '16_30_days'
                        ELSE 'above_30_days'
                    END AS aging_bucket,
                    -- Aging bucket display
                    CASE
                        WHEN (CURRENT_DATE - v.date) <= 7 THEN '0-7 Days'
                        WHEN (CURRENT_DATE - v.date) <= 15 THEN '8-15 Days'
                        WHEN (CURRENT_DATE - v.date) <= 30 THEN '16-30 Days'
                        ELSE '30+ Days'
                    END AS aging_bucket_display,
                    -- Pending type
                    CASE
                        WHEN v.state = 'requested' THEN 'approval'
                        WHEN v.state = 'paid' THEN 'reconciliation'
                    END AS pending_type
                FROM dev_petty_voucher v
                LEFT JOIN dev_petty_fund f ON f.id = v.fund_id
                WHERE v.state IN ('requested', 'paid')
            )
        """ % self._table)

    # ------------------
    # Action Methods
    # ------------------
    def action_open_voucher(self):
        """Open the related voucher form."""
        self.ensure_one()
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'dev.petty.voucher',
            'res_id': self.voucher_id.id,
            'view_mode': 'form',
            'target': 'current',
        }

    def action_export_xls(self):
        """Export aging report to XLS format."""
        import base64
        import io

        try:
            import xlsxwriter
        except ImportError:
            from odoo.exceptions import UserError
            raise UserError(
                'xlsxwriter library is required for Excel export. '
                'Install it using: pip install xlsxwriter'
            )

        output = io.BytesIO()
        workbook = xlsxwriter.Workbook(output, {'in_memory': True})
        worksheet = workbook.add_worksheet('Aging Report')

        # Define formats
        header_format = workbook.add_format({
            'bold': True,
            'bg_color': '#4472C4',
            'font_color': 'white',
            'border': 1,
            'align': 'center',
        })
        cell_format = workbook.add_format({'border': 1})
        money_format = workbook.add_format({'border': 1, 'num_format': '#,##0.00'})
        date_format = workbook.add_format({'border': 1, 'num_format': 'yyyy-mm-dd'})
        danger_format = workbook.add_format({'border': 1, 'bg_color': '#FFCCCC'})
        warning_format = workbook.add_format({'border': 1, 'bg_color': '#FFFFCC'})

        # Headers
        headers = ['Voucher', 'Fund', 'Requester', 'Date', 'Amount', 'Status', 'Days Pending', 'Aging Bucket']
        for col, header in enumerate(headers):
            worksheet.write(0, col, header, header_format)

        # Set column widths
        worksheet.set_column(0, 0, 15)  # Voucher
        worksheet.set_column(1, 1, 20)  # Fund
        worksheet.set_column(2, 2, 20)  # Requester
        worksheet.set_column(3, 3, 12)  # Date
        worksheet.set_column(4, 4, 15)  # Amount
        worksheet.set_column(5, 5, 20)  # Status
        worksheet.set_column(6, 6, 12)  # Days
        worksheet.set_column(7, 7, 15)  # Bucket

        # Data rows
        for row, record in enumerate(self, start=1):
            # Determine row format based on aging
            row_format = cell_format
            if record.aging_bucket == 'above_30_days':
                row_format = danger_format
            elif record.aging_bucket == '16_30_days':
                row_format = warning_format

            worksheet.write(row, 0, record.voucher_name or '', row_format)
            worksheet.write(row, 1, record.fund_name or '', row_format)
            worksheet.write(row, 2, record.requester_id.name or '', row_format)
            worksheet.write(row, 3, str(record.voucher_date) if record.voucher_date else '', date_format)
            worksheet.write(row, 4, record.amount or 0, money_format)
            worksheet.write(row, 5, record.state_display or '', row_format)
            worksheet.write(row, 6, record.days_pending or 0, row_format)
            worksheet.write(row, 7, record.aging_bucket_display or '', row_format)

        workbook.close()
        output.seek(0)

        # Create attachment
        attachment = self.env['ir.attachment'].create({
            'name': 'Petty_Cash_Aging_Report_%s.xlsx' % fields.Date.today(),
            'type': 'binary',
            'datas': base64.b64encode(output.read()),
            'mimetype': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
        })

        return {
            'type': 'ir.actions.act_url',
            'url': '/web/content/%s?download=true' % attachment.id,
            'target': 'new',
        }


class DevPettyCashAgingSummary(models.Model):
    """
    Petty Cash Aging Summary (SQL View).

    Provides aggregated aging summary by fund and bucket.
    """
    _name = 'dev.petty.cash.aging.summary'
    _description = 'Petty Cash Aging Summary'
    _auto = False
    _order = 'fund_name, aging_bucket'

    fund_id = fields.Many2one(
        'dev.petty.fund',
        string='Fund',
        readonly=True,
    )
    fund_name = fields.Char(
        string='Fund Name',
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
    pending_type = fields.Selection([
        ('approval', 'Pending Approval'),
        ('reconciliation', 'Pending Reconciliation'),
    ], string='Pending Type', readonly=True)
    aging_bucket = fields.Selection([
        ('0_7_days', '0-7 Days'),
        ('8_15_days', '8-15 Days'),
        ('16_30_days', '16-30 Days'),
        ('above_30_days', '30+ Days'),
    ], string='Aging Bucket', readonly=True)
    aging_bucket_display = fields.Char(
        string='Aging',
        readonly=True,
    )

    # Aggregates
    voucher_count = fields.Integer(
        string='Voucher Count',
        readonly=True,
    )
    total_amount = fields.Monetary(
        string='Total Amount',
        currency_field='currency_id',
        readonly=True,
    )
    avg_days_pending = fields.Float(
        string='Avg Days Pending',
        readonly=True,
        digits=(12, 1),
    )
    max_days_pending = fields.Integer(
        string='Max Days Pending',
        readonly=True,
    )

    def init(self):
        """Create or replace the SQL view."""
        tools.drop_view_if_exists(self.env.cr, self._table)
        self.env.cr.execute("""
            CREATE OR REPLACE VIEW %s AS (
                SELECT
                    ROW_NUMBER() OVER () AS id,
                    v.fund_id AS fund_id,
                    f.name AS fund_name,
                    v.company_id AS company_id,
                    f.currency_id AS currency_id,
                    CASE
                        WHEN v.state = 'requested' THEN 'approval'
                        WHEN v.state = 'paid' THEN 'reconciliation'
                    END AS pending_type,
                    CASE
                        WHEN (CURRENT_DATE - v.date) <= 7 THEN '0_7_days'
                        WHEN (CURRENT_DATE - v.date) <= 15 THEN '8_15_days'
                        WHEN (CURRENT_DATE - v.date) <= 30 THEN '16_30_days'
                        ELSE 'above_30_days'
                    END AS aging_bucket,
                    CASE
                        WHEN (CURRENT_DATE - v.date) <= 7 THEN '0-7 Days'
                        WHEN (CURRENT_DATE - v.date) <= 15 THEN '8-15 Days'
                        WHEN (CURRENT_DATE - v.date) <= 30 THEN '16-30 Days'
                        ELSE '30+ Days'
                    END AS aging_bucket_display,
                    COUNT(v.id) AS voucher_count,
                    COALESCE(SUM(v.amount), 0) AS total_amount,
                    COALESCE(AVG((CURRENT_DATE - v.date)), 0) AS avg_days_pending,
                    COALESCE(MAX((CURRENT_DATE - v.date))::INTEGER, 0) AS max_days_pending
                FROM dev_petty_voucher v
                LEFT JOIN dev_petty_fund f ON f.id = v.fund_id
                WHERE v.state IN ('requested', 'paid')
                GROUP BY
                    v.fund_id,
                    f.name,
                    v.company_id,
                    f.currency_id,
                    CASE
                        WHEN v.state = 'requested' THEN 'approval'
                        WHEN v.state = 'paid' THEN 'reconciliation'
                    END,
                    CASE
                        WHEN (CURRENT_DATE - v.date) <= 7 THEN '0_7_days'
                        WHEN (CURRENT_DATE - v.date) <= 15 THEN '8_15_days'
                        WHEN (CURRENT_DATE - v.date) <= 30 THEN '16_30_days'
                        ELSE 'above_30_days'
                    END,
                    CASE
                        WHEN (CURRENT_DATE - v.date) <= 7 THEN '0-7 Days'
                        WHEN (CURRENT_DATE - v.date) <= 15 THEN '8-15 Days'
                        WHEN (CURRENT_DATE - v.date) <= 30 THEN '16-30 Days'
                        ELSE '30+ Days'
                    END
            )
        """ % self._table)
