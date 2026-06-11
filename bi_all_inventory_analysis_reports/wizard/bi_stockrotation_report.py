# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.exceptions import UserError
from datetime import date, timedelta, datetime
import datetime
from odoo.tools import DEFAULT_SERVER_DATE_FORMAT
import tempfile
# from odoo.tools.misc import xlwt
import xlwt
import io
import base64
import time
from dateutil.relativedelta import relativedelta
from pytz import timezone


class Inventory_Stock_Rotation_analysis_wizard(models.Model):
    _name = 'inventory.stock.rotation.report.wiz'
    _description = 'Inventory Stock Rotation Analysis Report'


    from_date = fields.Date('From Date')
    to_date = fields.Date('To Date')
    company_ids = fields.Many2many("res.company", string="Company")
    category_ids = fields.Many2many("product.category", string="Product Category")
    product_ids = fields.Many2many("product.product", string="Product")
    warehouse_ids = fields.Many2many("stock.warehouse", string="Warehouse")
    from_beginning = fields.Boolean("date upto")
    date_upto = fields.Date("date of movements upto")

    @api.onchange('from_date', 'to_date', 'company_ids', 'category_ids', 'product_ids', 'warehouse_ids', 'from_beginning',
                  'date_upto')
    def onchange_data_set_company_domain(self):
        for rec in self:
            return {'domain': {'company_ids': [('id', 'in', self.env.user.company_ids.ids)]}}

    def print_inventory_stock_rotation_report(self):
        if self.to_date or self.from_date:
            if self.to_date <= self.from_date:
                raise UserError(_('End date should be greater than start date.'))

        filename = 'Stock Rotation Report' + '.xls'
        workbook = xlwt.Workbook()

        worksheet = workbook.add_sheet('Stock Rotation Report')
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
            0, 0, 0, 5, 'Stock Rotation Report', GREEN_TABLE_HEADER)

        row=1
        col=0
        worksheet.write(row, col, 'Company' or '', for_left)
        col=1
        for i in self.company_ids:
            company=[]
            company.append(i.name)
            worksheet.write(row, col, company or '', for_left_not_bold)
            col+=1

        row=2
        col=0
        worksheet.write(row, col, 'Warehouse' or '', for_left)
        col=1
        for i in self.warehouse_ids:
            warehouse=[]
            warehouse.append(i.name)
            worksheet.write(row, col, warehouse or '', for_left_not_bold)
            col+=1

            
        if self.from_beginning==True:
            self.to_date=self.date_upto
            self.from_date=date(2003, 9, 17)
            row = 3
            worksheet.write(row, 0, 'Stock Movement Upto' or '', for_left)
            worksheet.write(row, 1, self.date_upto.strftime('%d-%m-%Y') or '', for_left)

        else:
            row = 4
            worksheet.write(row, 0, 'Report start date' or '', for_left)
            worksheet.write(row, 1, self.from_date.strftime('%d-%m-%Y') or '', for_left)
            row = 5
            worksheet.write(row, 0, 'Report end date' or '', for_left)
            worksheet.write(row, 1, self.to_date.strftime('%d-%m-%Y') or '', for_left)


        row = 6

        worksheet.write(row, 0, 'Product Name' or '', for_left)
        worksheet.write(row, 1, 'Category' or '', for_left)
        worksheet.write(row, 2, 'Opening Stock' or '', for_left)
        worksheet.write(row, 3, 'Sales' or '', for_left)
        worksheet.write(row, 4, 'Sales Return' or '', for_left)
        worksheet.write(row, 5, 'Purchase' or '', for_left)
        worksheet.write(row, 6, 'Purchase Return' or '', for_left)
        worksheet.write(row, 7, 'Internal IN' or '', for_left)
        worksheet.write(row, 8, 'Internal OUT' or '', for_left)
        worksheet.write(row, 9, 'Adjustment IN' or '', for_left)
        worksheet.write(row, 10, 'Adjustment OUT' or '', for_left)
        worksheet.write(row, 11, 'Production IN' or '', for_left)
        worksheet.write(row, 12, 'Production OUT' or '', for_left)
        worksheet.write(row, 13, 'Transit IN' or '', for_left)
        worksheet.write(row, 14, 'Transit OUT' or '', for_left)
        worksheet.write(row, 15, 'Closing' or '', for_left)

        
       

        
        
        product_ids = self.env['product.product']

        if self.category_ids:
            product_ids = self.env['product.product'].search([('categ_id','in',self.category_ids.ids)])

        if self.product_ids:
            product_ids = self.product_ids

        if not product_ids:
            product_ids = self.env['product.product'].search([])


        stock_data = self.env['stock.quant'].search([])
        if self.warehouse_ids and not self.company_ids:
            warehouse_data = self.env['stock.warehouse'].search([('id','in',self.warehouse_ids.ids)])
        elif not self.warehouse_ids and self.company_ids:
            warehouse_data = self.env['stock.warehouse'].search([('company_id','in',self.company_ids.ids)])
        elif self.warehouse_ids and self.company_ids:
            warehouse_data = self.env['stock.warehouse'].search([('id','in',self.warehouse_ids.ids),('company_id','in',self.company_ids.ids)])
       
        else:
            warehouse_data = self.env['stock.warehouse'].search([])
        product_qty = self.env['stock.move.line'].search([])

        data = self.env['stock.picking'].search([('create_date', '>=', self.from_date),('create_date', '<=', self.to_date)])

        
        product_qty = self.env['stock.move.line'].search([('create_date', '>=', self.from_date),('create_date', '<=', self.to_date)])
        
        rows = 7
        sr_no = 0

        closing=0.0
        purchase_return=0.0
        

        for rec1 in product_ids:
            sale_return=0.0
            transit_in=0.0
            transit_out=0.0
            adjust_out=0.0
            adjust_in=0.0
            production_out=0.0
            production_in=0.0
            for record in stock_data:
                for warehouse in warehouse_data:

                    if rec1.id == record.product_id.id:
                        location_ids  = warehouse.lot_stock_id + warehouse.lot_stock_id.child_ids
                        if record.location_id in location_ids:
                            opening_qty=0.0
                            closing_qty=0.0
                            for qty in product_qty:
                                if rec1.id == qty.product_id.id:
                                    if str(qty.date.strftime("%m-%d-%y"))<=str(self.from_date.strftime("%m-%d-%y")):
                                        if qty.location_dest_id in location_ids:
                                            opening_qty+=qty.quantity
                                        if qty.location_id in location_ids:
                                            opening_qty = opening_qty-qty.quantity
                                    if str(qty.date.strftime("%m-%d-%y"))<=str(self.to_date.strftime("%m-%d-%y")):
                                        if qty.location_dest_id in location_ids:
                                            closing_qty+=qty.quantity
                                        if qty.location_id in location_ids:
                                            closing_qty = closing_qty-qty.quantity
                                        

                            for rec in data:
                                rec_moves = getattr(rec, 'move_ids', False) or getattr(rec, 'move_ids_without_package', self.env['stock.move'])
                                for product in rec_moves:
                                    if rec1.id == product.product_id.id:
                                        if product.state =='confirmed':
                                            sale_return+= product.product_uom_qty
                                        if product.state =='draft':
                                            transit_in+= product.product_uom_qty
                                        if product.state =='assigned':
                                            transit_out+= product.product_uom_qty
                            

                            
                            for i in rec1.stock_quant_ids:
                                if i.location_id.usage =='inventory':
                                    if i.quantity>0:
                                        adjust_out=i.quantity
                                    if i.quantity<0:
                                        adjust_in=i.quantity
                                if i.location_id.usage =='production':
                                    if i.quantity>0:
                                        production_in=i.quantity
                                    if i.quantity<0:
                                        production_out=i.quantity
                                        

                            sr_no += 1
                            worksheet.write(rows, 0, record.product_id.display_name or '', for_left_not_bold)
                            worksheet.write(rows, 1, rec1.categ_id.display_name or '', for_left_not_bold)
                            worksheet.write(rows, 2, record.inventory_quantity  or '0.0', for_left_not_bold)
                            worksheet.write(rows, 3, rec1.sales_count or '0.0', for_left_not_bold)
                            worksheet.write(rows, 4, sale_return or '0.0', for_left_not_bold)
                            worksheet.write(rows, 5, rec1.purchased_product_qty or '0.0', for_left_not_bold)
                            worksheet.write(rows, 6, purchase_return or '0.0', for_left_not_bold)
                            worksheet.write(rows, 7, rec1.incoming_qty or '0.0', for_left_not_bold)
                            worksheet.write(rows, 8, rec1.outgoing_qty or '0.0', for_left_not_bold)
                            worksheet.write(rows, 9, adjust_in or '0.0', for_left_not_bold)
                            worksheet.write(rows, 10, adjust_out or '0.0', for_left_not_bold)
                            worksheet.write(rows, 11, production_in or '0.0', for_left_not_bold)
                            worksheet.write(rows, 12, production_out or '0.0', for_left_not_bold)
                            worksheet.write(rows, 13, transit_in or '0.0', for_left_not_bold)
                            worksheet.write(rows, 14, transit_out or '0.0', for_left_not_bold)
                            worksheet.write(rows, 15, closing_qty or '0.0', for_left_not_bold)
                            rows += 1


           
        fp = io.BytesIO()
        workbook.save(fp)
        stock_rotation_id = self.env['inventory.stock.rotation.extended'].create(
            {'excel_file': base64.encodebytes(fp.getvalue()), 'file_name': filename})
        fp.close()

        return{
            'view_mode': 'form',
            'res_id': stock_rotation_id.id,
            'res_model': 'inventory.stock.rotation.extended',
            'type': 'ir.actions.act_window',
            'context': self._context,
            'target': 'new',
        }


class Inventory_Stock_Rotation_analysis_Extended(models.TransientModel):
    _name = 'inventory.stock.rotation.extended'
    _description = "Stock Rotation Excel Extended"

    excel_file = fields.Binary('Download Report :- ')
    file_name = fields.Char('Excel File', size=64)

    
