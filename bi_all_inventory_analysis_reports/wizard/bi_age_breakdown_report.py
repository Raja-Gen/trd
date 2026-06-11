# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from datetime import datetime
# from odoo.tools.misc import xlwt
import xlwt
import io
import base64
from dateutil.relativedelta import relativedelta

class Inventory_Age_Breakdown_analysis_wizard(models.Model):
    _name = 'inventory.age.breakdown.report.wiz'
    _description = 'Inventory Age Breakdown Analysis Report'

    company_ids = fields.Many2many("res.company", string="Company")
    category_ids = fields.Many2many("product.category", string="Product Category")
    product_ids = fields.Many2many("product.product", string="Product")
    days_breakdown = fields.Integer("Days for Breakdown", default=30)

    @api.onchange('category_ids', 'product_ids', 'company_ids', 'days_breakdown')
    def onchange_data_set_company_domain(self):
        for rec in self:
            return {'domain': {'company_ids': [('id', 'in', self.env.user.company_ids.ids)]}}


    def print_inventory_age_breakdown_report(self):

        filename = 'Stock Age Breakdown Report' + '.xls'
        workbook = xlwt.Workbook()

        worksheet = workbook.add_sheet('Stock Age Breakdown Report')
        font = xlwt.Font()
        font.bold = True
        for_left = xlwt.easyxf(
            "font: bold 1, color black; borders: top double, bottom double, left double, right double; align: horiz left")
        for_left_not_bold = xlwt.easyxf("font: color black; align: horiz left",num_format_str='0.00')
        for_center_bold = xlwt.easyxf(
            "font: bold 1, color black; align: horiz center")
        GREEN_TABLE_HEADER = xlwt.easyxf(
            'font: bold 1, name Tahoma, height 250;'
            'align: vertical center, horizontal center, wrap on;'
            'borders: top double, bottom double, left double, right double;'
        )
        style = xlwt.easyxf(
            'font:height 400, bold True, name Arial; align: horiz center, vert center;borders: top medium,right medium,bottom medium,left medium')
    
        alignment = xlwt.Alignment()  # Create Alignment
        alignment.horz = xlwt.Alignment.HORZ_RIGHT
        style = xlwt.easyxf('align: wrap yes')
        style.num_format_str = '0.00'

        worksheet.row(0).height = 500
        worksheet.col(0).width = 10000
        worksheet.col(1).width = 7000
        worksheet.col(2).width = 4000
        worksheet.col(3).width = 4000
        worksheet.col(4).width = 4000
        worksheet.col(5).width = 4000
        worksheet.col(6).width = 4000
        worksheet.col(7).width = 4000

        worksheet.write_merge(0, 0, 0, 25, 'Stock Age Breakdown Report', GREEN_TABLE_HEADER)

        row= 1
        col=0
        worksheet.write(row, col, 'Company' or '', for_left)
        col=1
        for i in self.company_ids:
            company=[]
            company.append(i.name)
            worksheet.write(row, col, company or '', for_left_not_bold)
            col+=1

        base_days = self.days_breakdown or 1
        if base_days <= 30:
            sales_columns = 2
        else:
            sales_columns = 3

        row += 1
        row_col = 10 + sales_columns
        worksheet.write_merge(row, row, 0, row_col - 1, '', for_left)
        initial_val = 1
        for break_down in range(1,7):
            initial_val = break_down if break_down == 1 else ((self.days_breakdown)*(break_down-1)) + 1
            worksheet.write_merge(row, row, row_col, row_col+1, str(initial_val) + ' To '+ str((self.days_breakdown)*break_down) or '', for_left)
            row_col += 2
        worksheet.write_merge(row,row, row_col,row_col+1, ' Oldest Then '+ str(initial_val + self.days_breakdown) or '', for_left)

        row += 1
        header_col = 0

        stock_str = 'Stock'
        value_str = 'Value'

        worksheet.write(row, header_col, 'Item Code', for_left)
        header_col += 1
        worksheet.write(row, header_col, 'Product Name' or '', for_left)
        header_col += 1
        worksheet.write(row, header_col, 'Brand', for_left)
        header_col += 1
        worksheet.write(row, header_col, 'Category' or '', for_left)
        header_col += 1
        worksheet.write(row, header_col, 'Expected Qty', for_left)
        header_col += 1

        worksheet.write(row, header_col, 'Cost', for_left)
        header_col += 1

        worksheet.write(row, header_col, 'Available Qty', for_left)
        header_col += 1

        worksheet.write(row, header_col, 'Available Stock Value', for_left)
        header_col += 1
        worksheet.write(row, header_col, 'Total Stock' or '', for_left)
        header_col += 1
        worksheet.write(row, header_col, 'Stock Value' or '', for_left)
        header_col += 1

        base_days = self.days_breakdown or 1

        if base_days <= 30:
            worksheet.write(row, header_col, f'Last {base_days} Days Sales', for_left)
            header_col += 1

            worksheet.write(row, header_col, 'Last Week Sales', for_left)
            header_col += 1

            sales_columns = 2
        else:
            worksheet.write(row, header_col, f'Last {base_days} Days Sales', for_left)
            header_col += 1

            worksheet.write(row, header_col, 'Last 30 Days Sales', for_left)
            header_col += 1

            worksheet.write(row, header_col, 'Last Week Sales', for_left)
            header_col += 1
            sales_columns = 3
        ageing_start_col = header_col

        for i in range(1,8):
            worksheet.write(row, header_col, stock_str, for_left)
            header_col += 1
            worksheet.write(row, header_col, value_str, for_left)
            header_col += 1

        product_ids = self.env['product.product']

        if self.category_ids:
            product_ids = self.env['product.product'].search([('categ_id','in',self.category_ids.ids)])

        if self.product_ids:
            product_ids = self.product_ids

        if not product_ids:
            product_ids = self.env['product.product'].search(['|', ('company_id', 'in', self.company_ids.ids), ('company_id', '=', False)])


        rows = row + 1

        stock_value = 0

        for product_id in product_ids:
            qty_to_carry = 0.0

            domain = [('product_id','=',product_id.id)]
            
            if self.company_ids:
                domain += [('company_id','in',self.company_ids.ids)]
            
            loc_domain = [('usage', 'in', ['internal'])]
            if self.company_ids:
                loc_domain += [('company_id','in',self.company_ids.ids)]

            location_id = self.env['stock.location'].search(loc_domain)
            location_dest_id = self.env['stock.location'].search(loc_domain)
            
            domain += [('location_id', 'in', location_id.ids)]
            domain += [('state','=','done')]
            
            move_lines = self.env['stock.move.line'].search(domain)
            qty_sold = sum(line.qty_done for line in move_lines)

            qty_to_carry = qty_sold

            col = 0
            worksheet.write(rows, col, product_id.default_code or '', for_left_not_bold)
            col += 1
            worksheet.write(rows, col, product_id.display_name or '', for_left_not_bold)
            col += 1
            brand_name = product_id.x_studio_brand_5.x_name if hasattr(product_id, 'x_studio_brand_5') and product_id.x_studio_brand_5 else ''
            worksheet.write(rows, col, brand_name, for_left_not_bold)
            col += 1
            worksheet.write(rows, col, product_id.categ_id.display_name or '', for_left_not_bold)
            col += 1
            worksheet.write(rows, col, product_id.virtual_available or '', for_left_not_bold)
            col += 1
            worksheet.write(rows, col, product_id.standard_price or '', for_left_not_bold)
            col += 1
            worksheet.write(rows, col, product_id.qty_available or '', for_left_not_bold)
            col += 1
            available_value = product_id.qty_available * product_id.standard_price
            worksheet.write(rows, col, available_value or '', for_left_not_bold)
            col += 1
            worksheet.write(rows, col, product_id.qty_available  or '', for_left_not_bold)
            col += 1
            stock_value = product_id.qty_available * product_id.standard_price
            worksheet.write(rows, col, stock_value or '', for_left_not_bold)
            col += 1
            today = fields.Datetime.now()
            base_days = self.days_breakdown or 1

            SaleLine = self.env['sale.order.line']

            def _get_sale_qty(days):
                from_date = today - relativedelta(days=days)
                domain = [
                    ('product_id', '=', product_id.id),
                    ('order_id.state', 'in', ['sale', 'done']),
                    ('order_id.date_order', '>=', from_date),
                ]
                if self.company_ids:
                    domain += [('order_id.company_id', 'in', self.company_ids.ids)]
                return sum(SaleLine.search(domain).mapped('product_uom_qty'))

            if base_days <= 30:
                period_sales = _get_sale_qty(base_days)
                week_sales = _get_sale_qty(7)
            else:
                period_sales = _get_sale_qty(base_days)
                month_sales = _get_sale_qty(30)
                week_sales = _get_sale_qty(7)

            if base_days <= 30:
                worksheet.write(rows, col, period_sales or '', for_left_not_bold)
                col += 1

                worksheet.write(rows, col, week_sales or '', for_left_not_bold)
                col += 1
            else:
                worksheet.write(rows, col, period_sales or '', for_left_not_bold)
                col += 1

                worksheet.write(rows, col, month_sales or '', for_left_not_bold)
                col += 1

                worksheet.write(rows, col, week_sales or '', for_left_not_bold)
                col += 1

            col = ageing_start_col + (7 * 2)


            for i in range(7, 0, -1):
                to_date = datetime.now() if i == 1 else (datetime.now() - relativedelta(days=self.days_breakdown*(i-1)))
                from_date = to_date - relativedelta(days=self.days_breakdown)

                domain = [('date','<=',str(to_date))]
                if i != 7:
                    domain += [('date','>',str(from_date))]

                domain += [('product_id','=',product_id.id)]
                domain += [('state','=','done')]
                if self.company_ids:
                    domain += [('company_id','in',self.company_ids.ids)]
                
                domain += [('location_dest_id', 'in', location_dest_id.ids)]

                move_lines = self.env['stock.move.line'].search(domain)

                qty_on_hand = sum(line.qty_done for line in move_lines)
                qty_to_carry -= qty_on_hand

                if qty_on_hand and (qty_to_carry < 0.0):
                    qty_on_hand = abs(qty_on_hand - (qty_on_hand - abs(qty_to_carry)))
                    qty_to_carry = 0.0
                if qty_to_carry > 0.0:
                    qty_on_hand = 0.0

                col -= 1
                worksheet.write(rows, col, abs(qty_on_hand) * product_id.standard_price  or '', for_left_not_bold)
                col -= 1
                worksheet.write(rows, col, abs(qty_on_hand) or '', for_left_not_bold)

            rows += 1

        fp = io.BytesIO()
        workbook.save(fp)
        age_breakdown_id = self.env['inventory.age.breakdown.extended'].create(
            {'excel_file': base64.encodebytes(fp.getvalue()), 'file_name': filename})
        fp.close()

        return{
            'view_mode': 'form',
            'res_id':age_breakdown_id.id,
            'res_model': 'inventory.age.breakdown.extended',
            'type': 'ir.actions.act_window',
            'context': self._context,
            'target': 'new',
        }


class Inventory_Age_Breakdown_analysis_Extended(models.TransientModel):
    _name = 'inventory.age.breakdown.extended'
    _description = "Stock Age Breakdown Excel Extended"

    excel_file = fields.Binary('Download Report :- ')
    file_name = fields.Char('Excel File', size=64)
