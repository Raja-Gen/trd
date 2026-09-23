# -*- coding: utf-8 -*-

from dateutil.relativedelta import relativedelta
from datetime import timedelta, datetime, time
import logging
import ast

from odoo import models, fields, api

_logger = logging.getLogger(__name__)


class AsKPI(models.Model):
    _name = 'as.kpi'
    _description = 'Business KPI'
    _order = 'name'

    # Fields
    name = fields.Char(required=True)
    technical_name = fields.Char(required=True)
    category_id = fields.Many2one(
        'as.kpi.category', string='Category', required=True
    )
    model_category = fields.Char(string='Model Category', required=True)
    sequence = fields.Integer(default=10)

    # ============================
    #        SALE ORDER
    # ============================
    def total_sales_orders(self):
        sales = self.env.context.get("preloaded_created_sales")
        return len(sales) if sales else 0

    def confirmed_sales_orders(self):
        sales = self.env.context.get("preloaded_confirmed_sales")
        if sales:
            return len(sales)
        return 0
    
    def draft_sales_orders(self):
        sales = self.env.context.get("preloaded_created_sales")
        if sales:
            drafts = sales.filtered(lambda s: s.state == "draft")
            return len(drafts)
        return 0


    def cancelled_sales_orders(self):
        sales = self.env.context.get("preloaded_created_sales")
        if sales:
            cancelled = sales.filtered(lambda s: s.state == "cancel")
            return len(cancelled)
        return 0

    def sent_quotations(self):
        sales = self.env.context.get("preloaded_created_sales")
        if sales:
            sent = sales.filtered(lambda s: s.state == "sent")
            return len(sent)
        return 0

    def expired_quotations(self):
        creation_domain = self.env.context.get("creation_domain") or []

        expire_domain = []
        for field, op, val in creation_domain:
            if field == "create_date":
                expire_domain.append((
                    "validity_date",
                    op,
                    val.date() if hasattr(val, "date") else val
                ))
            else:
                expire_domain.append((field, op, val))

        expire_domain.append(('state', 'in', ['draft', 'sent']))

        count = self.env["sale.order"].search_count(expire_domain)
        return count

    def total_revenue(self):
        """
        Calculate total untaxed revenue for confirmed sales orders.
        """
        confirmed = self.env.context.get("preloaded_confirmed_sales") or []

        if confirmed:
            total = sum(confirmed.mapped("amount_untaxed"))
            return round(total, 2)
        return 0.00


    def average_order_value(self):
        """
        Calculate average untaxed value per confirmed sales order.
        """
        confirmed = self.env.context.get("preloaded_confirmed_sales") or []

        total_orders = len(confirmed)
        if total_orders:
            total_revenue = sum(confirmed.mapped("amount_untaxed"))
            avg = total_revenue / total_orders
            return round(avg, 2)
        return 0.00

    def total_untaxed_amount(self):
        sales = self.env.context.get("preloaded_created_sales")
        if sales:
            total = sum(sales.mapped("amount_untaxed"))
            return round(total, 2)
        return 0.00

    def total_tax_amount(self):
        sales = self.env.context.get("preloaded_created_sales")
        if sales:
            total = sum(sales.mapped("amount_tax"))
            return round(total, 2)
        return 0.00

    def total_order_value(self):
        sales = self.env.context.get("preloaded_created_sales") or []
        if sales:
            total = sum(sales.mapped("amount_total"))
            return round(total, 2)
        return 0.00

    def average_order_untaxed_amount(self):
        sales = self.env.context.get("preloaded_created_sales") or []
        if sales:
            avg = sum(sales.mapped("amount_untaxed")) / len(sales)
            return round(avg, 2)
        return 0.00

    def average_order_tax_amount(self):
        sales = self.env.context.get("preloaded_created_sales") or []
        if sales:
            avg = sum(sales.mapped("amount_tax")) / len(sales)
            return round(avg, 2)
        return 0.00

    def average_order_total_amount(self):
        sales = self.env.context.get("preloaded_created_sales") or []
        if sales:
            avg = sum(sales.mapped("amount_total")) / len(sales)
            return round(avg, 2)
        return 0.00

    def maximum_order_value(self):
        sales = self.env.context.get("preloaded_created_sales") or []
        if sales:
            mx = max(sales.mapped("amount_total"))
            return round(mx, 2)
        return 0.00

    def minimum_order_value(self):
        sales = self.env.context.get("preloaded_created_sales") or []
        if sales:
            mn = min(sales.mapped("amount_total"))
            return round(mn, 2)
        return 0.00

    def orders_fully_delivered(self):
        sales = self.env.context.get("preloaded_confirmed_sales") or []
        if not sales:
            return 0
        
        sale_ids = tuple(sales.ids)
        if not sale_ids:
            return 0

        self.env.cr.execute("""
            SELECT COUNT(DISTINCT so.id)
            FROM sale_order so
            JOIN stock_picking sp ON sp.sale_id = so.id
            WHERE so.id IN %s
            GROUP BY so.id
            HAVING bool_and(sp.state = 'done')
        """, [sale_ids])

        count = len(self.env.cr.fetchall())
        return count

    
    def orders_partially_delivered(self):
        sales = self.env.context.get("preloaded_confirmed_sales")
        if not sales:
            return 0
        
        sale_ids = tuple(sales.ids)
        if not sale_ids:
            return 0

        self.env.cr.execute("""
            SELECT COUNT(DISTINCT so.id)
            FROM sale_order so
            JOIN stock_picking sp ON sp.sale_id = so.id
            WHERE so.id IN %s
            GROUP BY so.id
            HAVING bool_or(sp.state = 'done') AND NOT bool_and(sp.state = 'done')
        """, [sale_ids])

        count = len(self.env.cr.fetchall())
        return count

    def orders_waiting_delivery(self):
        sales = self.env.context.get("preloaded_confirmed_sales")
        if not sales:
            return 0
        
        sale_ids = tuple(sales.ids)
        if not sale_ids:
            return 0

        self.env.cr.execute("""
            SELECT COUNT(DISTINCT so.id)
            FROM sale_order so
            JOIN stock_picking sp ON sp.sale_id = so.id
            WHERE so.id IN %s
            GROUP BY so.id
            HAVING bool_and(sp.state IN ('waiting','confirmed','assigned'))
        """, [sale_ids])

        count = len(self.env.cr.fetchall())
        return count


    def orders_fully_invoiced(self):
        sales = self.env.context.get("preloaded_confirmed_sales")
        if not sales:
            return 0

        fully_invoiced = sales.filtered(lambda s: s.invoice_status == "invoiced")
        return len(fully_invoiced)

    def orders_to_invoice(self):
        sales = self.env.context.get("preloaded_confirmed_sales")
        if not sales:
            return 0

        to_invoice = sales.filtered(lambda s: s.invoice_status in ("to invoice", "partial"))
        return len(to_invoice)

    def orders_not_invoiced(self):
        sales = self.env.context.get("preloaded_confirmed_sales")
        if not sales:
            return 0

        not_invoiced = sales.filtered(lambda s: s.invoice_status == "no")
        return len(not_invoiced)


    def total_products_sold(self):
        sales = self.env.context.get("preloaded_confirmed_sales")
        if not sales:
            return 0

        sale_ids = tuple(sales.ids)
        if not sale_ids:
            return 0

        self.env.cr.execute("""
            SELECT COALESCE(SUM(sol.product_uom_qty), 0)
            FROM sale_order_line sol
            WHERE sol.order_id IN %s
        """, [sale_ids])

        total_qty = self.env.cr.fetchone()[0]
        return total_qty

    # ============================
    #     WEBSITE SALES
    # ============================
    
    def web_total_orders(self):
        sales = self.env.context.get("preloaded_web_created_sales")
        return len(sales) if sales else 0

    def web_confirmed_orders(self):
        sales = self.env.context.get("preloaded_web_confirmed_sales")
        if sales:
            return len(sales)
        return 0
    
    def web_draft_orders(self):
        sales = self.env.context.get("preloaded_web_created_sales")
        if sales:
            drafts = sales.filtered(lambda s: s.state == "draft")
            return len(drafts)
        return 0

    def web_cancelled_orders(self):
        sales = self.env.context.get("preloaded_web_created_sales")
        if sales:
            cancelled = sales.filtered(lambda s: s.state == "cancel")
            return len(cancelled)
        return 0

    def web_sent_quotations(self):
        sales = self.env.context.get("preloaded_web_created_sales")
        if sales:
            sent = sales.filtered(lambda s: s.state == "sent")
            return len(sent)
        return 0
    
    def web_expired_quotations(self):
        creation = self.env.context.get("web_creation_domain") or []

        expire_domain = []
        for field, op, val in creation:
            if field == "create_date":
                expire_domain.append((
                    "validity_date",
                    op,
                    val.date() if hasattr(val, "date") else val
                ))
            else:
                expire_domain.append((field, op, val))

        expire_domain.append(('state', 'in', ['draft', 'sent']))

        return self.env["sale.order"].search_count(expire_domain)

    def web_total_revenue(self):
        """
        Calculate total untaxed revenue for confirmed sales orders.
        """
        confirmed = self.env.context.get("preloaded_web_confirmed_sales") or []

        if confirmed:
            total = sum(confirmed.mapped("amount_untaxed"))
            return round(total, 2)
        return 0.00


    def web_average_order_value(self):
        """
        Calculate average untaxed value per confirmed sales order.
        """
        confirmed = self.env.context.get("preloaded_web_confirmed_sales") or []

        total_orders = len(confirmed)
        if total_orders:
            total_revenue = sum(confirmed.mapped("amount_untaxed"))
            avg = total_revenue / total_orders
            return round(avg, 2)
        return 0.00
    
    def web_total_untaxed(self):
        sales = self.env.context.get("preloaded_web_created_sales")
        if sales:
            total = sum(sales.mapped("amount_untaxed"))
            return round(total, 2)
        return 0.0

    def web_total_tax(self):
        sales = self.env.context.get("preloaded_web_created_sales")
        if sales:
            total = sum(sales.mapped("amount_tax"))
            return round(total, 2)
        return 0.0

    def web_total_value(self):
        sales = self.env.context.get("preloaded_web_created_sales")
        if sales:
            total = sum(sales.mapped("amount_total"))
            return round(total, 2)
        return 0.0

    def web_avg_untaxed(self):
        sales = self.env.context.get("preloaded_web_created_sales") or []
        if sales:
            avg = sum(sales.mapped("amount_untaxed")) / len(sales)
            return round(avg, 2)
        return 0.0

    def web_avg_tax(self):
        sales = self.env.context.get("preloaded_web_created_sales") or []
        if sales:
            avg = sum(sales.mapped("amount_tax")) / len(sales)
            return round(avg, 2)
        return 0.0

    def web_avg_total(self):
        sales = self.env.context.get("preloaded_web_created_sales") or []
        if sales:
            avg = sum(sales.mapped("amount_total")) / len(sales)
            return round(avg, 2)
        return 0.0

    def web_max_value(self):
        sales = self.env.context.get("preloaded_web_created_sales") or []
        if sales:
            mx = max(sales.mapped("amount_total"))
            return round(mx, 2)
        return 0.0

    def web_min_value(self):
        sales = self.env.context.get("preloaded_web_created_sales") or []
        if sales:
            mn = min(sales.mapped("amount_total"))
            return round(mn, 2)
        return 0.0

    def web_fully_delivered(self):
        sales = self.env.context.get("preloaded_web_confirmed_sales") or []
        if not sales:
            return 0

        sale_ids = tuple(sales.ids)
        self.env.cr.execute("""
            SELECT COUNT(DISTINCT so.id)
            FROM sale_order so
            JOIN stock_picking sp ON sp.sale_id = so.id
            WHERE so.id IN %s
            GROUP BY so.id
            HAVING bool_and(sp.state = 'done')
        """, [sale_ids])

        return len(self.env.cr.fetchall())

    def web_partially_delivered(self):
        sales = self.env.context.get("preloaded_web_confirmed_sales")
        if not sales:
            return 0

        sale_ids = tuple(sales.ids)
        self.env.cr.execute("""
            SELECT COUNT(DISTINCT so.id)
            FROM sale_order so
            JOIN stock_picking sp ON sp.sale_id = so.id
            WHERE so.id IN %s
            GROUP BY so.id
            HAVING bool_or(sp.state = 'done')
            AND NOT bool_and(sp.state = 'done')
        """, [sale_ids])

        return len(self.env.cr.fetchall())

    def web_waiting_delivery(self):
        sales = self.env.context.get("preloaded_web_confirmed_sales")
        if not sales:
            return 0

        sale_ids = tuple(sales.ids)
        self.env.cr.execute("""
            SELECT COUNT(DISTINCT so.id)
            FROM sale_order so
            JOIN stock_picking sp ON sp.sale_id = so.id
            WHERE so.id IN %s
            GROUP BY so.id
            HAVING bool_and(sp.state IN ('waiting', 'confirmed', 'assigned'))
            AND NOT bool_or(sp.state = 'done')
        """, [sale_ids])

        return len(self.env.cr.fetchall())

        
    def web_fully_invoiced(self):
        sales = self.env.context.get("preloaded_web_confirmed_sales")
        if sales:
            fully = sales.filtered(lambda s: s.invoice_status == "invoiced")
            return len(fully)
        return 0

    def web_to_invoiced(self):
        sales = self.env.context.get("preloaded_web_confirmed_sales")
        if sales:
            to_invoice = sales.filtered(lambda s: s.invoice_status in ("to invoice", "partial"))
            return len(to_invoice)
        return 0

    def web_not_invoiced(self):
        sales = self.env.context.get("preloaded_web_confirmed_sales")
        if sales:
            not_invoiced = sales.filtered(lambda s: s.invoice_status == "no")
            return len(not_invoiced)
        return 0

    def web_total_products_sold(self):
        sales = self.env.context.get("preloaded_web_confirmed_sales")
        if not sales:
            return 0

        sale_ids = tuple(sales.ids)
        self.env.cr.execute("""
            SELECT COALESCE(SUM(sol.product_uom_qty), 0)
            FROM sale_order_line sol
            WHERE sol.order_id IN %s
        """, [sale_ids])

        qty = self.env.cr.fetchone()[0]
        return qty

    def website_visitors_count(self):
        visitors = self.env.context.get("preloaded_web_visitors") or []
        if not visitors:
            return 0
        return len(visitors)

    def website_page_views(self):
        visitors = self.env.context.get("preloaded_web_visitors") or []
        if not visitors:
            return 0

        total_page_views = sum(visitors.mapped("visitor_page_count"))
        
        return total_page_views

    def website_product_views(self):
        visitors = self.env.context.get("preloaded_web_visitors") or []
        if not visitors:
            return 0

        total_product_views = sum(visitors.mapped("visitor_product_count"))
        
        return total_product_views

    # ============================
    #        Accounting methods
    # ============================

    def total_invoices_created(self):
        moves = self.env.context.get("preloaded_created_account") or self.env['account.move']
        
        if not moves:
            return 0

        created_invoices = moves.filtered_domain([
            ('move_type', '=', 'out_invoice')
        ])

        return len(created_invoices)

    def new_draft_invoices(self):
        moves = self.env.context.get("preloaded_created_account") or self.env['account.move']
        
        if not moves:
            return 0

        draft_invoices = moves.filtered_domain([
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'draft')
        ])

        return len(draft_invoices)

    def new_posted_invoices(self):
        moves = self.env.context.get("preloaded_created_account") or self.env['account.move']
        
        if not moves:
            return 0

        posted_invoices = moves.filtered_domain([
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted')
        ])

        return len(posted_invoices)

    def count_not_paid_invoices(self):
        moves = self.env.context.get("preloaded_account_moves") or self.env['account.move']
        if not moves:
            return 0

        not_paid_invoices = moves.filtered_domain([
            ('move_type', '=', 'out_invoice'),
            ('payment_state', '=', 'not_paid')
        ])
        return len(not_paid_invoices)

    def count_in_payment_invoices(self):
        moves = self.env.context.get("preloaded_account_moves") or self.env['account.move']
        if not moves:
            return 0

        in_payment_invoices = moves.filtered_domain([
            ('move_type', '=', 'out_invoice'),
            ('payment_state', '=', 'in_payment')
        ])
        return len(in_payment_invoices)

    def count_partial_invoices(self):
        moves = self.env.context.get("preloaded_account_moves") or self.env['account.move']
        if not moves:
            return 0

        partial_invoices = moves.filtered_domain([
            ('move_type', '=', 'out_invoice'),
            ('payment_state', '=', 'partial')
        ])
        return len(partial_invoices)

    def count_paid_invoices(self):
        moves = self.env.context.get("preloaded_account_moves") or self.env['account.move']
        if not moves:
            return 0

        paid_invoices = moves.filtered_domain([
            ('move_type', '=', 'out_invoice'),
            ('payment_state', '=', 'paid')
        ])
        return len(paid_invoices)
    
    def total_paid_invoice_amount(self):
        moves = self.env.context.get("preloaded_account_moves") or self.env['account.move']
        
        if not moves:
            return 0.0

        paid_invoices = moves.filtered_domain([
            ('move_type', '=', 'out_invoice'),
            ('payment_state', '=', 'paid')
        ])

        total_amount = sum(paid_invoices.mapped('amount_total'))
        return round(total_amount, 2)

    def total_posted_invoice_value(self):
        moves = self.env.context.get("preloaded_account_moves") or self.env['account.move']
        
        if not moves:
            return 0.0

        target_moves = moves.filtered_domain([
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted')
        ])

        return round(sum(target_moves.mapped('amount_total')), 2)

    def total_outstanding_amount(self):
        moves = self.env.context.get("preloaded_account_moves") or self.env['account.move']
        
        if not moves:
            return 0.0

        target_moves = moves.filtered_domain([
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted')
        ])

        total = sum(target_moves.mapped('amount_residual'))
        return round(total, 2)
    
    def total_untaxed_amount_invoice(self):
        moves = self.env.context.get("preloaded_account_moves") or self.env['account.move']
        
        if not moves:
            return 0.0

        untaxed_moves = moves.filtered_domain([
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted')
        ])

        return round(sum(untaxed_moves.mapped('amount_untaxed')), 2)

    def total_tax_amount_invoice(self):
        moves = self.env.context.get("preloaded_account_moves") or self.env['account.move']
        
        if not moves:
            return 0.0

        tax_moves = moves.filtered_domain([
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted')
        ])

        return round(sum(tax_moves.mapped('amount_tax')), 2)

    def avg_invoice_value(self):
        moves = self.env.context.get("preloaded_account_moves") or self.env['account.move']
        
        if not moves:
            return 0.0

        posted_moves = moves.filtered_domain([
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted')
        ])

        count = len(posted_moves)
        if not count:
            return 0.0

        total = sum(posted_moves.mapped('amount_total'))
        return round(total / count, 2)

    def avg_outstanding_amount(self):
        moves = self.env.context.get("preloaded_account_moves") or self.env['account.move']
        
        if not moves:
            return 0.0

        outstanding_moves = moves.filtered_domain([
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted')
        ])

        count = len(outstanding_moves)
        if not count:
            return 0.0

        total = sum(outstanding_moves.mapped('amount_residual'))
        return round(total / count, 2)


    # ============================
    #        Payments Overview
    # ============================

    def total_payment_transactions_count(self):
        transactions = self.env.context.get("preloaded_payment_transactions") or self.env['payment.transaction']
        if not transactions:
            return 0
        return len(transactions)

    def total_transaction_amount(self):
        transactions = self.env.context.get("preloaded_payment_transactions") or self.env['payment.transaction']
        if not transactions:
            return 0.0
        return round(sum(transactions.mapped('amount')), 2)

    def avg_transaction_amount(self):
        transactions = self.env.context.get("preloaded_payment_transactions") or self.env['payment.transaction']
        count = len(transactions)
        if not count:
            return 0.0
        total = sum(transactions.mapped('amount'))
        return round(total / count, 2)
    
    def total_customer_payments(self):
        payments = self.env.context.get("preloaded_account_payments") or self.env['account.payment']
        if not payments:
            return 0
        customers = payments.filtered_domain([('partner_type', '=', 'customer')])
        return len(customers)
    
    def total_customer_payment_amount(self):
        payments = self.env.context.get("preloaded_account_payments") or self.env['account.payment']
        if not payments:
            return 0.0

        customers = payments.filtered_domain([('partner_type', '=', 'customer')])
        
        return round(sum(customers.mapped('amount')), 2)

    def total_vendor_payments(self):
        payments = self.env.context.get("preloaded_account_payments") or self.env['account.payment']
        if not payments:
            return 0
        vendors = payments.filtered_domain([('partner_type', '=', 'supplier')])
        return len(vendors)

    def total_vendor_payment_amount(self):
        payments = self.env.context.get("preloaded_account_payments") or self.env['account.payment']
        if not payments:
            return 0.0
        vendors = payments.filtered_domain([('partner_type', '=', 'supplier')])
        return round(sum(vendors.mapped('amount')), 2)


    # --------------------V18/v19 ---START
    # In odoo version 17 there is no field state=inprocess/paid in account.payment
    def count_customer_payments_in_process(self):
        payments = self.env.context.get("preloaded_account_payments") or self.env['account.payment']
        if not payments:
            return 0
        in_process = payments.filtered_domain([
            ('partner_type', '=', 'customer'),
            ('state', '=', 'in_process')
        ])
        return len(in_process)

    def total_customer_payments_in_process_amount(self):
        payments = self.env.context.get("preloaded_account_payments") or self.env['account.payment']
        if not payments:
            return 0.0

        in_process = payments.filtered_domain([
            ('partner_type', '=', 'customer'),
            ('state', '=', 'in_process')
        ])
        
        return round(sum(in_process.mapped('amount')), 2)

    def count_customer_payments_paid(self):
        payments = self.env.context.get("preloaded_account_payments") or self.env['account.payment']
        if not payments:
            return 0
        posted = payments.filtered_domain([
            ('partner_type', '=', 'customer'),
            ('state', '=', 'paid')
        ])
        return len(posted)

    def total_customer_payments_paid_amount(self):
        payments = self.env.context.get("preloaded_account_payments") or self.env['account.payment']
        if not payments:
            return 0.0

        paid_payments = payments.filtered_domain([
            ('partner_type', '=', 'customer'),
            ('state', '=', 'paid')
        ])
        
        return round(sum(paid_payments.mapped('amount')), 2)

    def count_vendor_payments_in_process(self):
        payments = self.env.context.get("preloaded_account_payments") or self.env['account.payment']
        if not payments:
            return 0
        in_process = payments.filtered_domain([
            ('partner_type', '=', 'supplier'),
            ('state', '=', 'in_process')
        ])
        return len(in_process)

    def total_vendor_payments_in_process_amount(self):
        payments = self.env.context.get("preloaded_account_payments") or self.env['account.payment']
        if not payments:
            return 0.0
        in_process = payments.filtered_domain([
            ('partner_type', '=', 'supplier'),
            ('state', '=', 'in_process')
        ])
        return round(sum(in_process.mapped('amount')), 2)

    def count_vendor_payments_paid(self):
        payments = self.env.context.get("preloaded_account_payments") or self.env['account.payment']
        if not payments:
            return 0
        paid_vendors = payments.filtered_domain([
            ('partner_type', '=', 'supplier'),
            ('state', '=', 'paid')
        ])
        return len(paid_vendors)

    def total_vendor_payments_paid_amount(self):
        payments = self.env.context.get("preloaded_account_payments") or self.env['account.payment']
        if not payments:
            return 0.0
        paid_vendors = payments.filtered_domain([
            ('partner_type', '=', 'supplier'),
            ('state', '=', 'paid')
        ])
        return round(sum(paid_vendors.mapped('amount')), 2)

    # --------------------V18/v19 ---END

    # ============================
    #        POS OVERVIEW
    # ============================

    # --- Status Counts ---

    def count_new_pos_orders(self):
        orders = self.env.context.get("preloaded_pos_orders") or self.env['pos.order']
        if not orders:
            return 0
        return len(orders)

    def count_paid_pos_orders(self):
        orders = self.env.context.get("preloaded_pos_orders") or self.env['pos.order']
        if not orders:
            return 0
        return len(orders.filtered_domain([('state', '=', 'paid')]))

    def count_posted_pos_orders(self):
        orders = self.env.context.get("preloaded_pos_orders") or self.env['pos.order']
        if not orders:
            return 0
        return len(orders.filtered_domain([('state', '=', 'done')]))

    def count_cancelled_pos_orders(self):
        orders = self.env.context.get("preloaded_pos_orders") or self.env['pos.order']
        if not orders:
            return 0
        return len(orders.filtered_domain([('state', '=', 'cancel')]))

    # --- Invoice Status (Computed/Non-Stored) ---
    
    def count_pos_orders_to_invoice(self):
        orders = self.env.context.get("preloaded_pos_orders") or self.env['pos.order']
        if not orders:
            return 0
        return len(orders.filtered(lambda o: o.invoice_status == 'to_invoice'))

    def count_pos_orders_invoiced(self):
        orders = self.env.context.get("preloaded_pos_orders") or self.env['pos.order']
        if not orders:
            return 0
        return len(orders.filtered(lambda o: o.invoice_status == 'invoiced'))

    def total_pos_invoiced_amount(self):
        orders = self.env.context.get("preloaded_pos_orders") or self.env['pos.order']
        if not orders:
            return 0.0
        
        invoiced = orders.filtered(lambda o: o.invoice_status == 'invoiced')
        if not invoiced:
            return 0.0
            
        return round(sum(invoiced.mapped('amount_total')), 2)

    # --- Monetary Values ---

    def total_pos_amount(self):
        orders = self.env.context.get("preloaded_pos_orders") or self.env['pos.order']
        if not orders:
            return 0.0
        return round(sum(orders.mapped('amount_total')), 2)

    def total_pos_paid_amount(self):
        orders = self.env.context.get("preloaded_pos_orders") or self.env['pos.order']
        if not orders:
            return 0.0
        return round(sum(orders.mapped('amount_paid')), 2)
        
    def total_pos_tax_amount(self):
        orders = self.env.context.get("preloaded_pos_orders") or self.env['pos.order']
        if not orders:
            return 0.0
        return round(sum(orders.mapped('amount_tax')), 2)

    def avg_pos_order_value(self):
        orders = self.env.context.get("preloaded_pos_orders") or self.env['pos.order']
        count = len(orders)
        if not count:
            return 0.0
        return round(sum(orders.mapped('amount_total')) / count, 2)

    def total_pos_payments_count(self):
        payments = self.env.context.get("preloaded_pos_payments") or self.env['pos.payment']
        if not payments:
            return 0
        return len(payments)

    def total_pos_payments_amount(self):
        payments = self.env.context.get("preloaded_pos_payments") or self.env['pos.payment']
        if not payments:
            return 0.0
        return round(sum(payments.mapped('amount')), 2)

    def avg_pos_payment_amount(self):
        payments = self.env.context.get("preloaded_pos_payments") or self.env['pos.payment']
        count = len(payments)
        if not count:
            return 0.0
        total = sum(payments.mapped('amount'))
        return round(total / count, 2)


    # ============================
    #        Purchase OVERVIEW
    # ============================

    def count_draft_rfqs(self):
        orders = self.env.context.get("preloaded_purchase_orders") or self.env['purchase.order']
        if not orders:
            return 0
        return len(orders.filtered_domain([('state', '=', 'draft')]))

    def count_rfq_sent(self):
        orders = self.env.context.get("preloaded_purchase_orders") or self.env['purchase.order']
        if not orders:
            return 0
        return len(orders.filtered_domain([('state', '=', 'sent')]))

    # V19
    def count_confirmed_purchase_orders(self):
        orders = self.env.context.get("preloaded_purchase_orders") or self.env['purchase.order']
        if not orders:
            return 0
        # count = len(orders.filtered_domain([('state', 'in', ['purchase', 'done'])]))
        count = len(orders.filtered_domain([('state', 'in', ['purchase'])])) 
        return count

    def count_cancelled_purchase_orders(self):
        orders = self.env.context.get("preloaded_purchase_orders") or self.env['purchase.order']
        if not orders:
            return 0
        return len(orders.filtered_domain([('state', '=', 'cancel')]))

    # --- Purchase Order Financials (Confirmed) ---

    # Version19
    def total_purchase_order_amount(self):
        orders = self.env.context.get("preloaded_purchase_orders") or self.env['purchase.order']
        # confirmed = orders.filtered_domain([('state', 'in', ['purchase', 'done'])])
        confirmed = orders.filtered_domain([('state', 'in', ['purchase'])])
        if not confirmed:
            return 0.0
        return round(sum(confirmed.mapped('amount_total')), 2)

    def total_purchase_order_tax_amount(self):
        orders = self.env.context.get("preloaded_purchase_orders") or self.env['purchase.order']
        # confirmed = orders.filtered_domain([('state', 'in', ['purchase', 'done'])])
        confirmed = orders.filtered_domain([('state', 'in', ['purchase'])])
        if not confirmed:
            return 0.0
        return round(sum(confirmed.mapped('amount_tax')), 2)

    def total_purchase_order_untaxed_amount(self):
        orders = self.env.context.get("preloaded_purchase_orders") or self.env['purchase.order']
        # confirmed = orders.filtered_domain([('state', 'in', ['purchase', 'done'])])
        confirmed = orders.filtered_domain([('state', 'in', ['purchase'])])
        if not confirmed:
            return 0.0
        return round(sum(confirmed.mapped('amount_untaxed')), 2)

    def avg_purchase_order_amount(self):
        orders = self.env.context.get("preloaded_purchase_orders") or self.env['purchase.order']
        # confirmed = orders.filtered_domain([('state', 'in', ['purchase', 'done'])])
        confirmed = orders.filtered_domain([('state', 'in', ['purchase'])])
        count = len(confirmed)
        if not count:
            return 0.0
        return round(sum(confirmed.mapped('amount_total')) / count, 2)

    # --- RFQ Financials (Draft/Sent) ---

    def total_rfq_amount(self):
        orders = self.env.context.get("preloaded_purchase_orders") or self.env['purchase.order']
        rfqs = orders.filtered_domain([('state', 'in', ['draft', 'sent'])])
        if not rfqs:
            return 0.0
        return round(sum(rfqs.mapped('amount_total')), 2)

    def total_rfq_tax_amount(self):
        orders = self.env.context.get("preloaded_purchase_orders") or self.env['purchase.order']
        rfqs = orders.filtered_domain([('state', 'in', ['draft', 'sent'])])
        if not rfqs:
            return 0.0
        return round(sum(rfqs.mapped('amount_tax')), 2)

    def total_rfq_untaxed_amount(self):
        orders = self.env.context.get("preloaded_purchase_orders") or self.env['purchase.order']
        rfqs = orders.filtered_domain([('state', 'in', ['draft', 'sent'])])
        if not rfqs:
            return 0.0
        return round(sum(rfqs.mapped('amount_untaxed')), 2)

    def avg_rfq_amount(self):
        orders = self.env.context.get("preloaded_purchase_orders") or self.env['purchase.order']
        rfqs = orders.filtered_domain([('state', 'in', ['draft', 'sent'])])
        count = len(rfqs)
        if not count:
            return 0.0
        return round(sum(rfqs.mapped('amount_total')) / count, 2)

    # --- Billing Status (Computed Fields) ---

    def count_fully_billed_purchase_orders(self):
        orders = self.env.context.get("preloaded_purchase_orders") or self.env['purchase.order']
        if not orders:
            return 0
        return len(orders.filtered(lambda o: o.invoice_status == 'invoiced'))

    def count_waiting_bills_purchase_orders(self):
        orders = self.env.context.get("preloaded_purchase_orders") or self.env['purchase.order']
        if not orders:
            return 0
        return len(orders.filtered(lambda o: o.invoice_status == 'to invoice'))

    # ============================
    #        SALES DOMAIN
    # ============================
    def _get_creation_domain(self, duration, company_id=None):
        today = fields.Date.context_today(self)
        if duration == "day":
            start_date = today
        elif duration == "week":
            start_date = today - timedelta(days=7)
        elif duration == "month":
            start_date = today - timedelta(days=30)
        elif duration == "year":
            start_date = today - timedelta(days=365)
        else:
            return []

        start_dt = datetime.combine(start_date, time.min)
        end_dt = datetime.combine(today, time.max)

        domain = [
            ("create_date", ">=", start_dt),
            ("create_date", "<=", end_dt),
        ]

        if company_id:
            domain.append(("company_id", "=", company_id))

        return domain

    def _get_confirmation_domain(self, duration, company_id=None):
        today = fields.Date.context_today(self)

        if duration == "day":
            start_date = today
        elif duration == "week":
            start_date = today - timedelta(days=7)
        elif duration == "month":
            start_date = today - timedelta(days=30)
        elif duration == "year":
            start_date = today - timedelta(days=365)
        else:
            return []

        start_dt = datetime.combine(start_date, time.min)
        end_dt = datetime.combine(today, time.max)

        domain = [
            ("state", "=", "sale"),
            ("date_order", ">=", start_dt),
            ("date_order", "<=", end_dt),
        ]

        if company_id:
            domain.append(("company_id", "=", company_id))

        return domain


    # ============================
    #     WEBSITE SALES DOMAIN
    # ============================
    def _get_time_domain(self, duration, company_id=None):
        today = fields.Date.context_today(self)
        if duration == "day":
            start_date = today
        elif duration == "week":
            start_date = today - timedelta(days=7)
        elif duration == "month":
            start_date = today - timedelta(days=30)
        elif duration == "year":
            start_date = today - timedelta(days=365)
        else:
            return []
        
        start_dt = datetime.combine(start_date, time.min)
        end_dt = datetime.combine(today, time.max)

        domain = [
            ("create_date", ">=", start_dt),
            ("create_date", "<=", end_dt),
        ]
        if company_id:
            domain.append(("company_id", "=", company_id))

        return domain
    
    def _get_web_creation_domain(self, duration, company_id=None):
        today = fields.Date.context_today(self)
        if duration == "day":
            start_date = today
        elif duration == "week":
            start_date = today - timedelta(days=7)
        elif duration == "month":
            start_date = today - timedelta(days=30)
        elif duration == "year":
            start_date = today - timedelta(days=365)
        else:
            return []
        
        start_dt = datetime.combine(start_date, time.min)
        end_dt = datetime.combine(today, time.max)

        domain = [
            ("create_date", ">=", start_dt),
            ("create_date", "<=", end_dt),
            ("website_id", "!=", False),
        ]
        if company_id:
            domain.append(("company_id", "=", company_id))

        return domain

    def _get_web_confirmation_domain(self, duration, company_id=None):
        today = fields.Date.context_today(self)
        if duration == "day":
            start_date = today
        elif duration == "week":
            start_date = today - timedelta(days=7)
        elif duration == "month":
            start_date = today - timedelta(days=30)
        elif duration == "year":
            start_date = today - timedelta(days=365)
        else:
            return []

        start_dt = datetime.combine(start_date, time.min)
        end_dt = datetime.combine(today, time.max)

        domain = [
            ("state", "=", "sale"),
            ("date_order", ">=", start_dt),
            ("date_order", "<=", end_dt),
            ("website_id", "!=", False),
        ]

        if company_id:
            domain.append(("company_id", "=", company_id))

        return domain


    # ============================
    #        Accounting
    # ============================

    def _get_creation_domain_account(self, duration, company_id=None):
        today = fields.Date.context_today(self)
        if duration == "day":
            start_date = today
        elif duration == "week":
            start_date = today - timedelta(days=7)
        elif duration == "month":
            start_date = today - timedelta(days=30)
        elif duration == "year":
            start_date = today - timedelta(days=365)
        else:
            return []

        start_dt = datetime.combine(start_date, time.min)
        end_dt = datetime.combine(today, time.max)

        domain = [
            ("create_date", ">=", start_dt),
            ("create_date", "<=", end_dt),
        ]

        if company_id:
            domain.append(("company_id", "=", company_id))

        return domain

    def _get_account_move_domain(self, duration, company_id=None):
        today = fields.Date.context_today(self)
        if duration == "day":
            start_date = today
        elif duration == "week":
            start_date = today - timedelta(days=7)
        elif duration == "month":
            start_date = today - timedelta(days=30)
        elif duration == "year":
            start_date = today - timedelta(days=365)
        else:
            return []

        domain = [
                ("invoice_date", ">=", start_date),
                ("invoice_date", "<=", today),
            ]

        if company_id:
            domain.append(("company_id", "=", company_id))

        return domain


    # ============================
    #        Payments Domain
    # ============================
    def _get_payment_transactions_domain(self, duration, company_id=None):
        today = fields.Date.context_today(self)
        if duration == "day":
            start_date = today
        elif duration == "week":
            start_date = today - timedelta(days=7)
        elif duration == "month":
            start_date = today - timedelta(days=30)
        elif duration == "year":
            start_date = today - timedelta(days=365)
        else:
            return []

        start_dt = datetime.combine(start_date, time.min)
        end_dt = datetime.combine(today, time.max)

        domain = [
            ("create_date", ">=", start_dt),
            ("create_date", "<=", end_dt),
        ]

        if company_id:
            domain.append(("company_id", "=", company_id))

        return domain

    def _get_account_payments_domain(self, duration, company_id=None):
        today = fields.Date.context_today(self)
        if duration == "day":
            start_date = today
        elif duration == "week":
            start_date = today - timedelta(days=7)
        elif duration == "month":
            start_date = today - timedelta(days=30)
        elif duration == "year":
            start_date = today - timedelta(days=365)
        else:
            return []

        domain = [
            ("date", ">=", start_date),
            ("date", "<=", today),
        ]

        if company_id:
            domain.append(("company_id", "=", company_id))

        return domain


    # ============================
    #        POS Domain
    # ============================
    def _get_pos_order_domain(self, duration, company_id=None):
        today = fields.Date.context_today(self)
        
        if duration == "day":
            start_date = today
        elif duration == "week":
            start_date = today - timedelta(days=7)
        elif duration == "month":
            start_date = today - timedelta(days=30)
        elif duration == "year":
            start_date = today - timedelta(days=365)
        else:
            return []

        start_dt = datetime.combine(start_date, time.min)
        end_dt = datetime.combine(today, time.max)

        domain = [
            ("date_order", ">=", start_dt),
            ("date_order", "<=", end_dt),
        ]

        if company_id:
            domain.append(("company_id", "=", company_id))

        return domain

    def _get_pos_payment_domain(self, duration, company_id=None):
        today = fields.Date.context_today(self)
        
        if duration == "day":
            start_date = today
        elif duration == "week":
            start_date = today - timedelta(days=7)
        elif duration == "month":
            start_date = today - timedelta(days=30)
        elif duration == "year":
            start_date = today - timedelta(days=365)
        else:
            return []

        start_dt = datetime.combine(start_date, time.min)
        end_dt = datetime.combine(today, time.max)

        domain = [
            ("payment_date", ">=", start_dt),
            ("payment_date", "<=", end_dt),
        ]

        if company_id:
            domain.append(("company_id", "=", company_id))

        return domain

    # ============================
    #        PURCHASE Domain
    # ============================
    def _get_purchase_order_domain(self, duration, company_id=None):
        today = fields.Date.context_today(self)
        
        if duration == "day":
            start_date = today
        elif duration == "week":
            start_date = today - timedelta(days=7)
        elif duration == "month":
            start_date = today - timedelta(days=30)
        elif duration == "year":
            start_date = today - timedelta(days=365)
        else:
            return []

        start_dt = datetime.combine(start_date, time.min)
        end_dt = datetime.combine(today, time.max)

        domain = [
            ("create_date", ">=", start_dt),
            ("create_date", "<=", end_dt),
        ]

        if company_id:
            domain.append(("company_id", "=", company_id))

        return domain

    # ============================
    #        CRON METHOD
    # ============================
    @api.model
    def cron_send_kpi_report(self):
        config = self.env["ir.config_parameter"].sudo()

        # Check KPI activation
        activate = config.get_param("business_kpi_report.activate_kpi")
        if not activate or activate in ["False", "0"]:
            return

        # Read config params
        kpi_param = config.get_param("business_kpi_report.kpi_ids")
        user_param = config.get_param("business_kpi_report.send_user_ids")
        send_via = config.get_param("business_kpi_report.send_via")
        duration = config.get_param("business_kpi_report.duration")
        email_tmpl = config.get_param("business_kpi_report.email_template_id") or self.env.ref("business_kpi_report.email_template_daily_kpi_report").id
        sms_tmpl = config.get_param("business_kpi_report.sms_template_id") or self.env.ref("business_kpi_report.sms_template_daily_kpi_report").id

        if not kpi_param or not user_param:
            return

        # Convert params to records
        kpi_ids = ast.literal_eval(kpi_param) if kpi_param else []
        user_ids = ast.literal_eval(user_param) if user_param else []

        kpi_recs = self.browse(kpi_ids).sorted(key='sequence')
        if not kpi_recs:
            return
        
        users = self.env["res.users"].browse(user_ids)
        
        company_ids = ast.literal_eval(config.get_param("business_kpi_report.company_ids") or "[]")
        if company_ids:
            companies = self.env['res.company'].browse(company_ids)
        else:
            companies = self.env['res.company'].search([])

        # Determine which KPI categories are requested so we only preload relevant data
        selected_model_categories = set((k.model_category or "other_model_category") for k in kpi_recs)

        for company in companies:
            # Prepare an empty context; populate only keys that are needed by requested KPI categories
            ctx = {}

            # Sales Overview preloads
            if 'sale_order' in selected_model_categories:
                creation_domain = self._get_creation_domain(duration, company.id)
                confirmation_domain = self._get_confirmation_domain(duration, company.id)
                preloaded_created = self.env["sale.order"].search(creation_domain)
                preloaded_confirmed = self.env["sale.order"].search(confirmation_domain)
                ctx.update({
                    "preloaded_created_sales": preloaded_created,
                    "preloaded_confirmed_sales": preloaded_confirmed,
                    "creation_domain": creation_domain,
                    "confirmation_domain": confirmation_domain,
                })

            # Website Sales Overview (orders) preloads
            if 'website_sale_order' in selected_model_categories:
                web_creation_domain = self._get_web_creation_domain(duration, company.id)
                web_confirmation_domain = self._get_web_confirmation_domain(duration, company.id)

                preloaded_web_created = self.env["sale.order"].search(web_creation_domain)
                preloaded_web_confirmed = self.env["sale.order"].search(web_confirmation_domain)

                ctx.update({
                    "preloaded_web_created_sales": preloaded_web_created,
                    "preloaded_web_confirmed_sales": preloaded_web_confirmed,
                    "web_creation_domain": web_creation_domain,
                    "web_confirmation_domain": web_confirmation_domain,
                })

            # Website Overview (visitor metrics) preloads
            if 'website_visitor' in selected_model_categories:
                time_domain = self._get_time_domain(duration)
                visitors = self.env["website.visitor"].search(time_domain)
                preloaded_web_visitors = visitors.filtered(lambda v: v.website_id.company_id.id == company.id)

                ctx.update({
                    "preloaded_web_visitors": preloaded_web_visitors,
                })

            # Accounting Overview preloads
            if 'account_move' in selected_model_categories:
                creation_domain_account = self._get_creation_domain_account(duration, company.id)
                preloaded_created_account = self.env["account.move"].search(creation_domain_account)

                account_move_domain = self._get_account_move_domain(duration, company.id)
                preloaded_account_moves = self.env["account.move"].search(account_move_domain)

                ctx.update({
                    "preloaded_created_account": preloaded_created_account,
                    "account_move_domain": account_move_domain,
                    "preloaded_account_moves": preloaded_account_moves,
                })

            # Payments Transaction preloads
            if 'payment_transaction' in selected_model_categories:
                
                payment_transactions_domain = self._get_payment_transactions_domain(duration, company.id)
                preloaded_payment_transactions = self.env["payment.transaction"].search(payment_transactions_domain)

                ctx.update({
                    "preloaded_payment_transactions": preloaded_payment_transactions,
                })

            # Account Payments preloads
            if 'account_payment' in selected_model_categories:

                account_payments_domain = self._get_account_payments_domain(duration, company.id)
                preloaded_account_payments = self.env["account.payment"].search(account_payments_domain)

                ctx.update({
                    "preloaded_account_payments": preloaded_account_payments,
                })

            # POS Order preloads
            if 'pos_order' in selected_model_categories:
                pos_order_domain = self._get_pos_order_domain(duration, company.id)
                preloaded_pos_orders = self.env["pos.order"].search(pos_order_domain)

                ctx.update({
                    "preloaded_pos_orders": preloaded_pos_orders,
                })

            # POS Payment preloads
            if 'pos_payment' in selected_model_categories:

                pos_payment_domain = self._get_pos_payment_domain(duration, company.id)
                preloaded_pos_payments = self.env["pos.payment"].search(pos_payment_domain)

                ctx.update({
                    "preloaded_pos_payments": preloaded_pos_payments,
                })

            # Purchase Order preloads
            if 'purchase_order' in selected_model_categories:
                purchase_order_domain = self._get_purchase_order_domain(duration, company.id)
                preloaded_purchase_orders = self.env["purchase.order"].search(purchase_order_domain)
                ctx.update({
                    "preloaded_purchase_orders": preloaded_purchase_orders,
                })

            duration_map = {
                'day': 'Daily',
                'week': 'Weekly',
                'month': 'Monthly',
                'year': 'Yearly',
            }
            duration_label = duration_map.get(duration) if duration else ''

            kpi_data = {}
            other_category = "Other Category"
            for kpi in kpi_recs:
                category = kpi.category_id.name if kpi.category_id else other_category
                if category not in kpi_data:
                    kpi_data[category] = []
                method_name = kpi.technical_name
                if hasattr(self, method_name):
                    method = getattr(self.with_context(ctx), method_name)
                    kpi_data[category].append({
                        'name': kpi.name,
                        'value': method()
                    })
            send_email = send_sms = False
            if not send_via:
                send_email = send_sms = True
            elif send_via == "email":
                send_email = True
            elif send_via == "sms":
                send_sms = True
            
            # EMAIL
            if send_email and email_tmpl:
                template = self.env["mail.template"].browse(int(email_tmpl))
                for user in users:
                    try:
                        template.with_context(kpi_data=kpi_data, company_name=company.name, user_name=user.name, duration_label=duration_label).send_mail(user.id, force_send=True)
                    except Exception as e:
                        _logger.error(
                            "Failed to send KPI Email to user %s for company %s: %s",
                            user.name, company.name, str(e)
                        )

            # SMS
            if send_sms and sms_tmpl:
                template = self.env["sms.template"].browse(int(sms_tmpl))

                for user in users:
                    partner = user.partner_id
                    phone = partner.phone
                    if not phone:
                        continue

                    try:
                        kpi_data_str = ""
                        for category, kpis in kpi_data.items():
                            kpi_data_str += f"{category}:\n"
                            for kpi in kpis:
                                kpi_data_str += f"{kpi['name']}: {kpi['value']}\n"
                            kpi_data_str += "\n"

                        sms_body_dict = template._render_template(
                            template.body,
                            'res.partner',
                            [partner.id],
                            add_context={
                                'kpi_data_str': kpi_data_str,
                                'user_name': user.name,
                                'company_name': company.name,
                                'duration_label': duration_label,
                            }
                        )

                        sms_body = sms_body_dict.get(partner.id)

                        sms = self.env['sms.sms'].create({
                            'body': sms_body,
                            'number': phone,
                            'partner_id': partner.id,
                            'state': 'outgoing',
                        })

                        sms._send()

                    except Exception as e:
                        _logger.error(
                            "Failed to send KPI SMS to user %s (%s): %s",
                            user.name, phone, str(e)
                        )