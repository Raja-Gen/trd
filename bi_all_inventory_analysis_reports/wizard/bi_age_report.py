# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import UserError
from datetime import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import tempfile
from odoo.tools.misc import xlwt
import io
import base64
from dateutil.relativedelta import relativedelta
from pytz import timezone


class Inventory_Age_analysis_wizard(models.Model):
    _name = 'inventory.age.report.wiz'
    _description = 'Inventory Age Analysis Report'


    company_ids = fields.Many2many("res.company", string="Company")
    category_ids = fields.Many2many("product.category", string="Product Category")
    product_ids = fields.Many2many("product.product", string="Product")

    @api.onchange('category_ids', 'product_ids', 'company_ids')
    def onchange_data_set_company_domain(self):
        for rec in self:
            return {'domain': {'company_ids': [('id', 'in', self.env.user.company_ids.ids)]}}
    
    def print_inventory_age_report(self):

        filename = 'Stock Age Report' + '.xls'
        workbook = xlwt.Workbook()

        worksheet = workbook.add_sheet('Stock Age Report')
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


       
        worksheet.write_merge(
            0, 0, 0, 5, 'Stock Age Report', GREEN_TABLE_HEADER)
        row = 1
        col=0
        worksheet.write(row, col, 'Company' or '', for_left)
        col=1
        for i in self.company_ids:
            company=[]
            company.append(i.name)
            worksheet.write(row, col, company or '', for_left_not_bold)
            col+=1

        

        row = 2

        worksheet.write(row, 0, 'Product Name' or '', for_left)
        worksheet.write(row, 1, 'Category' or '', for_left)
        worksheet.write(row, 2, 'Current Stock' or '', for_left)
        worksheet.write(row, 3, 'Stock Value' or '', for_left)
        worksheet.write(row, 4, 'Stock Value(%)' or '', for_left)
        worksheet.write(row, 5, 'Stock qty(%)' or '', for_left)
        worksheet.write(row, 6, 'Oldest Stock Age' or '', for_left)
        worksheet.write(row, 7, 'Oldest Qty' or '', for_left)
        worksheet.write(row, 8, 'Oldest Stock Value' or '', for_left)

        
        if self.category_ids and not self.product_ids:
            product_category = self.env['product.product'].search([('categ_id','in',self.category_ids.ids)])
        
        elif self.category_ids and self.product_ids:    
            product_category = self.env['product.product'].search([('categ_id','in',self.category_ids.ids),('id','in',self.product_ids.ids)])
        
        elif not self.category_ids and self.product_ids:
            product_category = self.env['product.product'].search([('id','in',self.product_ids.ids)])
        
        else:
            product_category = self.env['product.product'].search([])
        stock_data = self.env['stock.quant'].search([])
        if self.company_ids:
            warehouse_data = self.env['stock.warehouse'].search([('company_id', 'in', self.company_ids.ids)])
        else:
            warehouse_data = self.env['stock.warehouse'].search([])

        rows = 3
        sr_no = 0
        total_value=0.0
        
        quant=0.0
        total_qty=0.0
        value = 0
        quant_per=0.0
        stock_per=0.0
        latest_qty=0.0
        oldest_stock_qty=0.0

        for data in product_category:
            if data.qty_available and data.standard_price:
                value = data.qty_available * data.standard_price
            total_value += value
            total_qty+= data.qty_available

        
        for rec1 in product_category:
            for record in stock_data:
                for warehouse in warehouse_data:

                    if rec1.id == record.product_id.id:
                        location_ids  = warehouse.lot_stock_id + warehouse.lot_stock_id.child_ids
                        if record.location_id in location_ids:
            
                            f_date = datetime.now()
                            l_date = rec1.create_date
                            delta = f_date - l_date
                            
                            
                            if rec1.qty_available and rec1.standard_price:
                                value = rec1.qty_available * rec1.standard_price
                            else:
                                value=0.0

                            if value and total_value:
                                stock_per =(value/total_value)*100
                            else:
                                stock_per=0.0

                            if rec1.qty_available and total_qty:
                                quant_per =(rec1.qty_available/total_qty)*100
                            else:
                                quant_per=0.0

                            oldest_value=0.0
                            for i in rec1.stock_quant_ids:
                                if rec1.create_date <= rec1.write_date:
                                    latest_qty= i.quantity
                                    
                            
                            oldest_stock_qty= rec1.qty_available-latest_qty
                            if oldest_stock_qty:
                                oldest_value=oldest_stock_qty*rec1.standard_price
                            

                            # for data in stock:

                            sr_no += 1
                            worksheet.write(rows, 0, rec1.display_name or '', for_left_not_bold)
                            worksheet.write(rows, 1, rec1.categ_id.name_get()[0][1] or '', for_left_not_bold)
                            worksheet.write(rows, 2, rec1.qty_available  or '0.0', for_left_not_bold)
                            worksheet.write(rows, 3, value or '0.0', for_left_not_bold)
                            worksheet.write(rows, 4, quant_per or '0.0', for_left_not_bold)
                            worksheet.write(rows, 5, stock_per or '0.0', for_left_not_bold)
                            worksheet.write(rows, 6, delta.days or '0.0', for_left_not_bold)
                            worksheet.write(rows, 7, oldest_stock_qty or '0.0', for_left_not_bold)
                            worksheet.write(rows, 8, oldest_value or '0.0', for_left_not_bold)
                            rows +=1


           
        fp = io.BytesIO()
        workbook.save(fp)
        age_id = self.env['inventory.age.extended'].create(
            {'excel_file': base64.encodebytes(fp.getvalue()), 'file_name': filename})
        fp.close()

        return{
            'view_mode': 'form',
            'res_id':age_id.id,
            'res_model': 'inventory.age.extended',
            'type': 'ir.actions.act_window',
            'context': self._context,
            'target': 'new',
        }

    def tree_graph_report_view(self):
        if self.category_ids and not self.product_ids:
            product_category = self.env['product.product'].search([('categ_id','in',self.category_ids.ids)])
        
        elif self.category_ids and self.product_ids:    
            product_category = self.env['product.product'].search([('categ_id','in',self.category_ids.ids),('id','in',self.product_ids.ids)])
        
        elif not self.category_ids and self.product_ids:
            product_category = self.env['product.product'].search([('id','in',self.product_ids.ids)])
        
        else:
            product_category = self.env['product.product'].search([])
        stock_data = self.env['stock.quant'].search([])
        if self.company_ids:
            warehouse_data = self.env['stock.warehouse'].search([('company_id', 'in', self.company_ids.ids)])
        else:
            warehouse_data = self.env['stock.warehouse'].search([])

        record_set = self.env['inventory.age.extended'].search([])
        record_set.unlink()
        total_value=0.0
        total_qty=0.0
        value = 0
        quant_per=0.0
        stock_per=0.0
        latest_qty=0.0
        oldest_stock_qty=0.0
        for data in product_category:
            if data.qty_available and data.standard_price:
                value = data.qty_available * data.standard_price
            total_value += value
            total_qty+= data.qty_available

        for rec1 in product_category:
            inv_obj = self.env['inventory.age.extended']
            self.ensure_one()
            for record in stock_data:
                for warehouse in warehouse_data:

                    if rec1.id == record.product_id.id:
                        location_ids  = warehouse.lot_stock_id + warehouse.lot_stock_id.child_ids
                        if record.location_id in location_ids:

                            f_date = datetime.now()
                            l_date = rec1.create_date
                            delta = f_date - l_date
                            
                            
                            if rec1.qty_available and rec1.standard_price:
                                value = rec1.qty_available * rec1.standard_price
                            else:
                                value=0.0

                            if value and total_value:
                                stock_per =(value/total_value)*100
                            else:
                                stock_per=0.0

                            if rec1.qty_available and total_qty:
                                quant_per =(rec1.qty_available/total_qty)*100
                            else:
                                quant_per=0.0

                            oldest_value=0.0
                            for i in rec1.stock_quant_ids:
                                if rec1.create_date <= rec1.write_date:
                                    latest_qty= i.quantity
                                    
                            
                            oldest_stock_qty= rec1.qty_available-latest_qty
                            if oldest_stock_qty:
                                oldest_value=oldest_stock_qty*rec1.standard_price
                            

                            dispaly_data = inv_obj.create({
                                'products': rec1.id,
                                'product_category': rec1.categ_id.id,
                                'company': warehouse.company_id.id,
                                'stock_available': rec1.qty_available,
                                'value': value,
                                'days': delta.days,
                                'oldest_qty': oldest_stock_qty,
                                'oldest_value': oldest_value,
                                'qty_ratio': quant_per,
                                'value_ratio': stock_per,
                                
                            })

        display=[]
        graph_id = self.env.ref('bi_all_inventory_analysis_reports.inventory_age_extended_report_graph').id
        tree_id = self.env.ref('bi_all_inventory_analysis_reports.inventory_age_extended_report_tree').id
        graph_first = self.env.context.get('report_graph',False)

        if graph_first:
            display.append((graph_id, 'graph'))
            display.append((tree_id, 'tree'))
        else:
            display.append((tree_id, 'tree'))
            display.append((graph_id, 'graph'))
        return {
            'name': _('Stock age Ratio Analysis'),
            'res_model': 'inventory.age.extended',
            'view_mode': 'tree',
            'type': 'ir.actions.act_window',
            'views': display,
        }
    

class Inventory_Age_analysis_Extended(models.TransientModel):
    _name = 'inventory.age.extended'
    _description = "Stock Age Excel Extended"

    excel_file = fields.Binary('Download Report :- ')
    file_name = fields.Char('Excel File', size=64)

    products = fields.Many2one("product.product", "Product")
    product_category = fields.Many2one("product.category", "Category")
    warehouse = fields.Many2one("stock.warehouse")
    company = fields.Many2one("res.company", "Company")
    stock_available = fields.Float("Current Stock")
    value = fields.Float("Stock Value")
    days = fields.Integer("Oldest Stock Age")
    oldest_qty = fields.Float("Oldest Stock Qty")
    oldest_value  = fields.Float("Oldest Stock Value")
    qty_ratio = fields.Float("Stock Qty (%)")
    value_ratio = fields.Float("Stock Value (%)")
    wizard_id = fields.Many2one("inventory.age.report.wiz")
