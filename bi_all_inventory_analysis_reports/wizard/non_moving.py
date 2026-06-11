# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

import base64
from odoo import api, fields, models, _
from datetime import date
import io
from dateutil.relativedelta import relativedelta
from odoo.exceptions import UserError

try:
    import xlwt
except ImportError:
    xlwt = None

class NonMovingProductWizard(models.Model):
    _name = "non.moving.product.wizard"
    _description = "Description for NonMovingProductWizard"
    
    start_date = fields.Datetime('Start Period', required=True)
    end_date = fields.Datetime('End Period', required=True)
    warehouse = fields.Many2many('stock.warehouse', 'wh_wiz_rel_non_mov', 'wh', 'wiz', string='Warehouse',required=True)
    

    def diff_days(self, date1, date2):
        return (date1 - date2).days

    def _find_opening_qty(self, product):
        domain = [('product_id','=',product.id)]
        location_domain = [('usage', 'in', ['internal'])]

        location_id = self.env['stock.location']
        if self.warehouse:
            location_id = self.warehouse.mapped('lot_stock_id')
            location_id += location_id.mapped('child_ids')
        
        if not location_id:
            location_id = self.env['stock.location'].search(location_domain)
        
        domain += [('location_dest_id', 'in', location_id.ids)]
        domain += [('state','=','done')]

        date_start = self.start_date

        domain += [('date','<',date_start)]

        move_lines = self.env['stock.move.line'].search(domain)
        qty_sold = sum(move_lines.mapped('qty_done'))
        return qty_sold

    def _find_incoming_qty(self, product):

        domain = [('product_id','=',product.id)]

        location_domain = [('usage', 'in', ['internal'])]

        location_id = self.env['stock.location']
        if self.warehouse:
            location_id = self.warehouse.mapped('lot_stock_id')
            location_id += location_id.mapped('child_ids')

        if not location_id:
            location_id = self.env['stock.location'].search(location_domain)

        domain += [('location_dest_id', 'in', location_id.ids)]
        domain += [('state','=','done')]

        date_start = self.start_date
        date_end = self.end_date

        total_days = self.diff_days(self.end_date, self.start_date)

        product_sold_qty_per_month = []

        add_days = int(total_days / 5)

        date_start = self.start_date
        date_end = date_start + relativedelta(days=add_days)

        domain += [('date','>',date_start),('date','<=',date_end)]

        move_lines = self.env['stock.move.line'].search(domain)
        qty_sold = sum(move_lines.mapped('qty_done'))

        product_sold_qty_per_month.append(qty_sold)

        for i in range(1, 5):
            range_domain = [('product_id','=',product.id)]
            range_domain += [('location_dest_id', 'in', location_id.ids)]
            range_domain += [('state','=','done')]

            date_start = date_start + relativedelta(days=add_days)
            date_end = date_start + relativedelta(days=add_days)

            range_domain += [('date','>',date_start),('date','<=',date_end)]

            move_lines = self.env['stock.move.line'].search(range_domain)
            qty_sold = sum(move_lines.mapped('qty_done'))

            product_sold_qty_per_month.append(qty_sold)

        return product_sold_qty_per_month

    def print_exl_report(self):
        if self.end_date or self.start_date:
            if self.end_date <= self.start_date:
                raise UserError(_('End date should be greater than start date.'))

        filename = 'Non Moving Products Report.xls'
        get_warehouse_name = ', '.join(self.warehouse.mapped('name'))

        workbook = xlwt.Workbook()
        stylePC = xlwt.XFStyle()
        alignment = xlwt.Alignment()
        alignment.horz = xlwt.Alignment.HORZ_CENTER
        fontP = xlwt.Font()

        date_format = xlwt.XFStyle()
        date_format.num_format_str = 'dd/mm/yyyy'

        fontP.bold = True
        fontP.height = 200
        stylePC.font = fontP
        stylePC.num_format_str = '@'
        stylePC.alignment = alignment
        style_title = xlwt.easyxf("font:height 300; font: name Liberation Sans, bold on,color black; align: horiz center")
        style_table_header = xlwt.easyxf("font:height 200; font: name Liberation Sans, bold on,color black; align: horiz center")
        style = xlwt.easyxf("font:height 200; font: name Liberation Sans,color black;")
        worksheet = workbook.add_sheet('Sheet 1')
        worksheet.write_merge(3, 3, 1, 2,'Start Date:', style_table_header)
        worksheet.write_merge(4, 4, 1, 2,self.start_date, date_format)
        worksheet.write_merge(3, 3, 3, 4,'End Date', style_table_header)
        worksheet.write_merge(4, 4, 3, 4,self.end_date, date_format)
        worksheet.write_merge(3, 3, 5, 6,'Warehouse(s)', style_table_header)
        worksheet.write_merge(4, 4, 5, 6,get_warehouse_name, stylePC)
        worksheet.write_merge(0, 1, 1, 5, "Non Moving Products Report", style=style_title)
        worksheet.write_merge(6, 6, 0, 1, 'Product ID', style_table_header)
        worksheet.write_merge(6, 6, 2, 3, 'Default Code', style_table_header)
        worksheet.write_merge(6, 6, 4, 5, 'Product Name', style_table_header)
        worksheet.write_merge(6, 6, 6, 7, 'Available Qty', style_table_header)
        worksheet.write(6, 8, 'Last Sale Time', style_table_header)
        worksheet.write_merge(6, 6, 9, 10,'Duration From Last Sale In Days', style_table_header)
        rows = 7
        prod_col = 0
        domain = []

        date_start = self.start_date
        date_end = self.end_date

        product_ids = self.env['product.product'].search(domain, order='stock_value asc')

        location_id = self.env['stock.location']
        if self.warehouse:
            location_id = self.warehouse.mapped('lot_stock_id')
            location_id += location_id.mapped('child_ids')

        today = fields.Datetime.today()

        for product in product_ids:

            domain = [('product_id','=',product.id)]

            location_domain = [('usage', 'in', ['internal'])]

            if not location_id:
                location_id = self.env['stock.location'].search(location_domain)

            domain += [('location_id', 'in', location_id.ids)]
            domain += [('state','=','done')]

            domain += [('date','>',date_start),('date','<=',date_end)]

            demand_move_lines = self.env['stock.move.line'].search(domain)

            total_opening_qty = self._find_opening_qty(product)

            total_incoming_qty_list = self._find_incoming_qty(product)

            average_qty = round(sum(total_incoming_qty_list) / len(total_incoming_qty_list), 2)

            total_outgoing_demand_qty = sum(demand_move_lines.mapped('qty_done'))

            turnover_ration = total_outgoing_demand_qty / (average_qty or 1)

            movement_type = ''

            if turnover_ration < 1:
                movement_type = 'non'

            if movement_type != 'non':
                continue

            line_id = self.env['sale.order.line'].search([('product_id','=',product.id),('order_id.state','in',['sale','done'])],order='create_date desc', limit=1)

            date_order = line_id.order_id.date_order or today
            last_sale_day = abs(self.diff_days(today, date_order))
            worksheet.write_merge(rows, rows, prod_col,  prod_col+1, product.id, style)
            worksheet.write_merge(rows, rows, prod_col+2, prod_col+3, product.default_code or '', style)
            worksheet.write_merge(rows, rows, prod_col+4, prod_col+5, product.name, style)
            worksheet.write_merge(rows, rows, prod_col+6, prod_col+7, product.qty_available, style)
            worksheet.write(rows, prod_col+8, str(date_order) if date_order and date_order != today else 'Not Sold', date_format)
            worksheet.write_merge(rows, rows, prod_col+9, prod_col+10, str(last_sale_day) or '', style)
            rows = rows + 1

        rows = 6
        prod_col = 7
        fp = io.BytesIO()
        workbook.save(fp)
        
        export_id = self.env['non.moving.report.excel'].create({'excel_file': base64.encodebytes(fp.getvalue()), 'file_name': filename})
        res = {
            'view_mode': 'form',
            'res_id': export_id.id,
            'res_model': 'non.moving.report.excel',
            'view_type': 'form',
            'type': 'ir.actions.act_window',
            'target':'new'
        }
        return res


class non_moving_report_excel(models.TransientModel):
    _name = "non.moving.report.excel"
    _description = "Description for non_moving_report_excel"
    
    
    excel_file = fields.Binary('Excel Report For Non Moving Product')
    file_name = fields.Char('Excel File', size=64)



# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
