# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.tools.misc import xlwt
import io
import base64
from dateutil.relativedelta import relativedelta
from statistics import mean , stdev
from odoo.exceptions import UserError


class StockWarehouse(models.Model):
    _inherit = 'stock.warehouse'


    @api.model
    def _name_search(self, name, domain=None, operator='ilike', limit=100, order=None):
        domain = domain or []
        if self._context.get('fsn_xyz_company_id') and self._context.get('fsn_xyz_company_id'):
            company_ids = self._context.get('fsn_xyz_company_id')
            domain = [('company_id', 'in', company_ids)]
        return super()._name_search(name, domain, operator, limit, order)


class Inventory_fsn_xyz_analysis_wizard(models.Model):
    _name = 'inventory.fsn_xyz.report.wiz'
    _description = 'Inventory FSN XYZ Analysis Report'


    from_date = fields.Date('From Date')
    to_date = fields.Date('To Date')
    company_ids = fields.Many2many("res.company", string="Company")
    movement_type = fields.Selection([('all', 'All'),
                                            ('Fast_moving', 'Fast Moving'),
                                            ('Slow_moving', 'Slow Moving'),
                                            ('Non_moving', 'Non Moving')], "Classification For FSN", default="all")
    type = fields.Selection([('all', 'All'),
                                            ('X_class', 'X Class'),
                                            ('Y_class', 'Y Class'),
                                            ('Z_class', 'Z Class')], "Classification For XYZ", default="all")
    category_ids = fields.Many2many("product.category", string="Product Category")
    product_ids = fields.Many2many("product.product", string="Product")
    warehouse_ids = fields.Many2many("stock.warehouse", string="Warehouse")

    @api.onchange('from_date', 'to_date', 'company_ids', 'movement_type', 'type', 'category_ids', 'product_ids', 'warehouse_ids')
    def onchange_data_set_company_domain(self):
        for rec in self:
            return {'domain': {'company_ids': [('id', 'in', self.env.user.company_ids.ids)]}}

    def _get_fsn_report_data(self, product):

        date_start = self.from_date
        date_end = self.to_date

        domain = [('product_id','=',product.id)]
        
        location_domain = [('usage', 'in', ['internal'])]

        if self.company_ids:
            domain += [('company_id','in',self.company_ids.ids)]
            location_domain += [('company_id','in',self.company_ids.ids)]

        location_id = self.env['stock.location']

        if self.warehouse_ids:
            location_id = self.warehouse_ids.mapped('lot_stock_id')
            location_id += location_id.mapped('child_ids')
        else:
            location_id = self.env['stock.location'].search(location_domain)

        location_id = self.env['stock.location'].search(location_domain)
        
        domain += [('location_id', 'in', location_id.ids)]
        domain += [('state','=','done')]

        domain += [('date','>',date_start),('date','<=',date_end)]

        demand_move_lines = self.env['stock.move.line'].search(domain)

        total_opening_qty = self._find_opening_qty(product)

        total_incoming_qty_list = self._find_incoming_qty(product)

        average_qty = round(sum(total_incoming_qty_list) / len(total_incoming_qty_list), 2)

        total_outgoing_demand_qty = sum(demand_move_lines.mapped('quantity'))

        turnover_ration = total_outgoing_demand_qty / (average_qty or 1)

        movement_type = 'non'

        if turnover_ration >= 3:
            movement_type = 'fast'
        elif turnover_ration >=1 and turnover_ration < 3:
            movement_type = 'slow'
        elif turnover_ration < 1:
            movement_type = 'non'

        return total_opening_qty, average_qty, total_outgoing_demand_qty, turnover_ration, movement_type

    def _get_xyz_report_data(self, product):
        domain = [('product_id','=',product.id)]
        
        if self.company_ids:
            domain += [('company_id','in',self.company_ids.ids)]

        location_id = self.env['stock.location']

        if self.warehouse_ids:
            location_id = self.warehouse_ids.mapped('lot_stock_id')
            location_id += location_id.mapped('child_ids')
        else:
            location_id = self.env['stock.location'].search([('usage', 'in', ['internal'])])

        domain += [('location_id', 'in', location_id.ids)]
        domain += [('state','=','done')]

        total_days = self.diff_days(self.to_date, self.from_date)

        product_sold_qty_per_month = []

        add_days = int(total_days / 7)

        date_start = self.from_date
        date_end = date_start + relativedelta(days=add_days)

        domain += [('date','>',date_start),('date','<=',date_end)]

        move_lines = self.env['stock.move.line'].search(domain)
        qty_sold = sum(move_lines.mapped('quantity'))

        product_sold_qty_per_month.append(qty_sold)

        for i in range(1, 7):
            range_domain = [('product_id','=',product.id)]
            range_domain += [('location_id', 'in', location_id.ids)]
            range_domain += [('state','=','done')]

            date_start = date_start + relativedelta(days=add_days)
            date_end = date_start + relativedelta(days=add_days)

            range_domain += [('date','>',date_start),('date','<=',date_end)]

            move_lines = self.env['stock.move.line'].search(range_domain)
            qty_sold = sum(move_lines.mapped('quantity'))

            product_sold_qty_per_month.append(qty_sold)

        coefficient_of_variation = self.coefficient_of_variation(product_sold_qty_per_month)

        xyz_classification = 'Z'

        if coefficient_of_variation >= 0 and coefficient_of_variation < 13:
            xyz_classification = 'X'
        elif coefficient_of_variation >= 13 and coefficient_of_variation <= 28:
            xyz_classification = 'Y'
        else:
            xyz_classification = 'Z'

        return coefficient_of_variation, xyz_classification


    def diff_days(self, date1, date2):
        return (date1 - date2).days

    def coefficient_of_variation(self, args):
        stdev_ = stdev(args)
        mean_ = mean(args)
        coefficient_of_variation = round(stdev_ / (mean_ or 1) * 100)
        return coefficient_of_variation


    def _find_opening_qty(self, product):
        domain = [('product_id','=',product.id)]
            
        if self.company_ids:
            domain += [('company_id','in',self.company_ids.ids)]
        
        location_id = self.env['stock.location'].search([('usage', 'in', ['internal'])])

        domain += [('location_dest_id', 'in', location_id.ids)]
        domain += [('state','=','done')]

        date_start = self.from_date
        domain += [('date','<',date_start)]

        move_lines = self.env['stock.move.line'].search(domain)
        qty_sold = sum(move_lines.mapped('quantity'))
        return qty_sold

    def _find_incoming_qty(self, product):

        domain = [('product_id','=',product.id)]
            
        if self.company_ids:
            domain += [('company_id','in',self.company_ids.ids)]
        
        location_id = self.env['stock.location'].search([('usage', 'in', ['internal'])])
        
        domain += [('location_dest_id', 'in', location_id.ids)]
        domain += [('state','=','done')]

        date_start = self.from_date
        date_end = self.to_date

        total_days = self.diff_days(self.to_date, self.from_date)

        product_sold_qty_per_month = []

        add_days = int(total_days / 5)

        date_start = self.from_date
        date_end = date_start + relativedelta(days=add_days)

        domain += [('date','>',date_start),('date','<=',date_end)]

        move_lines = self.env['stock.move.line'].search(domain)
        qty_sold = sum(move_lines.mapped('quantity'))

        product_sold_qty_per_month.append(qty_sold)

        for i in range(1, 5):

            range_domain = [('product_id','=',product.id)]
            range_domain += [('location_dest_id', 'in', location_id.ids)]
            range_domain += [('state','=','done')]

            date_start = date_start + relativedelta(days=add_days)
            date_end = date_start + relativedelta(days=add_days)

            range_domain += [('date','>',date_start),('date','<=',date_end)]

            move_lines = self.env['stock.move.line'].search(range_domain)
            qty_sold = sum(move_lines.mapped('quantity'))

            product_sold_qty_per_month.append(qty_sold)

        return product_sold_qty_per_month
    

    def print_inventory_fsn_xyz_report(self):

        if self.to_date or self.from_date:
            if self.to_date <= self.from_date:
                raise UserError(_('End date should be greater than start date.'))

        filename = 'FSN XYZ Analysis Report' + '.xls'
        workbook = xlwt.Workbook()

        worksheet = workbook.add_sheet('FSN XYZ Analysis Report')
        font = xlwt.Font()
        font.bold = True
        for_left = xlwt.easyxf(
            "font: bold 1, color black; borders: top double, bottom double, left double, right double; align: horiz left")
        for_left_not_bold = xlwt.easyxf("font: color black; align: horiz left",num_format_str='0.00')

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
        worksheet.col(8).width = 4000
        worksheet.col(9).width = 4000
       
        worksheet.write_merge(0, 0, 0, 5, 'FSN XYZ Analysis Report', GREEN_TABLE_HEADER)

        row=2
        col=0
        worksheet.write(row, col, 'Company' or '', for_left)
        col=1
        for i in self.company_ids:
            company=[]
            company.append(i.name)
            worksheet.write(row, col, company or '', for_left_not_bold)
            col+=1
        
        row=3
        col=0
        worksheet.write(row, col, 'Warehouse' or '', for_left)
        col=1
        
        for i in self.warehouse_ids:
            warehouse=[]
            warehouse.append(i.name)
            worksheet.write(row, col, warehouse or '', for_left_not_bold)
            col+=1
        
        row = 4
        worksheet.write(row, 0, 'Report start date' or '', for_left)
        worksheet.write(row, 1, self.from_date.strftime('%d-%m-%Y') or '', for_left)
        row = 5
        worksheet.write(row, 0, 'Report end date' or '', for_left)
        worksheet.write(row, 1, self.to_date.strftime('%d-%m-%Y') or '', for_left)


        row = 6

        worksheet.write(row, 0, 'Product Name' or '', for_left)
        worksheet.write(row, 1, 'Category' or '', for_left)
        worksheet.write(row, 2, 'Average Stock' or '', for_left)
        worksheet.write(row, 3, 'Sales' or '', for_left)
        worksheet.write(row, 4, 'Turnover Ratio' or '', for_left)
        worksheet.write(row, 5, 'Current Stock' or '', for_left)
        worksheet.write(row, 6, 'Stock Value' or '', for_left)
        worksheet.write(row, 7, 'FSN Classification' or '', for_left)
        worksheet.write(row, 8, 'XYZ Classification' or '', for_left)
        worksheet.write(row, 9, 'FSN XYZ Classification' or '', for_left)


        domain = []
        if self.category_ids:
            domain += [('categ_id', 'in', self.category_ids.ids)]

        if self.product_ids:
            domain += [('id', 'in', self.product_ids.ids)]

        if self.company_ids:
            domain += ['|', ('company_id', 'in', self.company_ids.ids), ('company_id', '=', False)]

        product_ids = self.env['product.product'].search(domain, order='stock_value asc')

        rows = 7

        for product in product_ids:
            coefficient_of_variation, xyz_classification = self._get_xyz_report_data(product)
            total_opening_qty, average_qty, total_outgoing_demand_qty, turnover_ration, movement_type = self._get_fsn_report_data(product)

            if movement_type == 'fast':
                fsn_xyz_type = 'F' + xyz_classification
            elif movement_type == 'slow':
                fsn_xyz_type = 'S' + xyz_classification
            elif movement_type == 'non':
                fsn_xyz_type = 'N' + xyz_classification

            if self.type == 'all':
                pass
            if self.type == 'X_class' and xyz_classification != 'X':
                continue
            elif self.type == 'Y_class' and xyz_classification != 'Y':
                continue
            elif self.type == 'Z_class' and xyz_classification != 'Z':
                continue

            if self.movement_type == 'all':
                pass
            if self.movement_type == 'Fast_moving' and movement_type != 'fast':
                continue
            elif self.movement_type == 'Slow_moving' and movement_type != 'slow':
                continue
            elif self.movement_type == 'Non_moving' and movement_type != 'non':
                continue

            worksheet.write(rows, 0, product.name_get()[0][1] or '', for_left_not_bold)
            worksheet.write(rows, 1, product.categ_id.name_get()[0][1] or '', for_left_not_bold)
            worksheet.write(rows, 2, average_qty  or '0', for_left_not_bold)
            worksheet.write(rows, 3, total_outgoing_demand_qty or '0', for_left_not_bold)
            worksheet.write(rows, 4, turnover_ration or '0', for_left_not_bold)
            worksheet.write(rows, 5, product.qty_available or '0', for_left_not_bold)
            worksheet.write(rows, 6, product.qty_available * product.standard_price or '0', for_left_not_bold)
            worksheet.write(rows, 7, movement_type or '', for_left_not_bold)
            worksheet.write(rows, 8, xyz_classification or '', for_left_not_bold)
            worksheet.write(rows, 9, fsn_xyz_type or '', for_left_not_bold)

            rows += 1

        fp = io.BytesIO()
        workbook.save(fp)
        fsn_xyz_id = self.env['inventory.fsn_xyz.extended'].create(
            {'excel_file': base64.encodebytes(fp.getvalue()), 'file_name': filename})
        fp.close()

        return{
            'view_mode': 'form',
            'res_id': fsn_xyz_id.id,
            'res_model': 'inventory.fsn_xyz.extended',
            'type': 'ir.actions.act_window',
            'context': self._context,
            'target': 'new',
        }

   
    def tree_graph_report_view(self):

        if self.to_date or self.from_date:
            if self.to_date <= self.from_date:
                raise UserError(_('End date should be greater than start date.'))

        fsn_xyz_obj = self.env['inventory.fsn_xyz.extended']
        record_set = fsn_xyz_obj.search([])
        record_set.unlink()
        
        domain = []
        if self.category_ids:
            domain += [('categ_id', 'in', self.category_ids.ids)]

        if self.product_ids:
            domain += [('id', 'in', self.product_ids.ids)]

        if self.company_ids:
            domain += ['|', ('company_id', 'in', self.company_ids.ids), ('company_id', '=', False)]

        product_ids = self.env['product.product'].search(domain, order='stock_value asc')

        rows = 7

        for product in product_ids:
            coefficient_of_variation, xyz_classification = self._get_xyz_report_data(product)
            total_opening_qty, average_qty, total_outgoing_demand_qty, turnover_ration, movement_type = self._get_fsn_report_data(product)

            if self.type == 'all':
                pass
            if self.type == 'X_class' and xyz_classification != 'X':
                continue
            elif self.type == 'Y_class' and xyz_classification != 'Y':
                continue
            elif self.type == 'Z_class' and xyz_classification != 'Z':
                continue

            if self.movement_type == 'all':
                pass
            if self.movement_type == 'Fast_moving' and movement_type != 'fast':
                continue
            elif self.movement_type == 'Slow_moving' and movement_type != 'slow':
                continue
            elif self.movement_type == 'Non_moving' and movement_type != 'non':
                continue

            xyz_classification_ = 'Z_class'

            if xyz_classification == 'X':
                xyz_classification_ = 'X_class'
            elif xyz_classification == 'Y':
                xyz_classification_ = 'Y_class'
            elif xyz_classification_ == 'Z':
                xyz_classification_ = 'Z_class'

            if movement_type == 'fast':
                fsn_xyz_type = 'F' + xyz_classification
                movement_type = 'Fast_moving'
            elif movement_type == 'slow':
                fsn_xyz_type = 'S' + xyz_classification
                movement_type = 'Slow_moving'
            elif movement_type == 'non':
                fsn_xyz_type = 'N' + xyz_classification
                movement_type = 'Non_moving'

            if self.company_ids:
                company_ids = self.company_ids
            else:
                company_ids = self.env['res.company'].sudo().search([])

            dispaly_data = fsn_xyz_obj.create({
                'products': product.id,
                'product_category': product.categ_id.id,
                # 'company': self.env.user.company_id.id,
                'company_ids': company_ids.ids,
                'stock_average': average_qty,
                'stock_available': product.qty_available,
                'value': product.qty_available * product.standard_price,
                'sales': total_outgoing_demand_qty,
                'turnover': turnover_ration,
                'movement_type': movement_type,
                'type': xyz_classification_,
                'fsn_xyz_type': fsn_xyz_type,
            })

        display=[]
        graph_id = self.env.ref('bi_all_inventory_analysis_reports.inventory_fsn_xyz_extended_report_graph').id
        tree_id = self.env.ref('bi_all_inventory_analysis_reports.inventory_fsn_xyz_extended_report_tree').id
        graph_first = self.env.context.get('report_graph',False)

        if graph_first:
            display.append((graph_id, 'graph'))
            display.append((tree_id, 'tree'))
        else:
            display.append((tree_id, 'tree'))
            display.append((graph_id, 'graph'))
        return {
            'name': _('Stock FSN XYZ Analysis'),
            'res_model': 'inventory.fsn_xyz.extended',
            'view_mode': 'tree',
            'type': 'ir.actions.act_window',
            'views': display,
        }
    

class Inventory_fsn_xyz_analysis_Extended(models.TransientModel):
    _name = 'inventory.fsn_xyz.extended'
    _description = "Stock FSN XYZ Excel Extended"

    excel_file = fields.Binary('Download Report :- ')
    file_name = fields.Char('Excel File', size=64)

    products = fields.Many2one("product.product", "Product")
    product_category = fields.Many2one("product.category", "Category")
    # company = fields.Many2one("res.company", "Company")
    company_ids = fields.Many2many("res.company", 'rel_company_fsn', 'company_id', 'fsn_id', string="Company")
    stock_average = fields.Float("Average Stock")
    sales = fields.Float("Sales")
    turnover = fields.Float("Turnover Ratio")
    stock_available = fields.Float("Current Stock")
    value = fields.Float("Stock Value")
    movement_type = fields.Selection([('all', 'All'),
                                            ('Fast_moving', 'Fast Moving'),
                                            ('Slow_moving', 'Slow Moving'),
                                            ('Non_moving', 'Non Moving')], "Classification For FSN", default="all")
    type = fields.Selection([('all', 'All'),
                                            ('X_class', 'X Class'),
                                            ('Y_class', 'Y Class'),
                                            ('Z_class', 'Z Class')], "Classification For XYZ", default="all")
    fsn_xyz_type = fields.Char("Classification For FSN-XYZ")
    wizard_id = fields.Many2one("inventory.fsn_xyz.report.wiz")




class FSN_XYZ_Inherit_Product_Product(models.Model):
    _inherit = 'product.product'

    stock_value = fields.Float("stock Value" ,compute='calculate_stock_value')

    @api.depends('standard_price','qty_available')
    def calculate_stock_value(self):
        if self.standard_price and self.qty_available:
            self.stock_value=  self.standard_price*self.qty_available
        else:
            self.stock_value=0.0
