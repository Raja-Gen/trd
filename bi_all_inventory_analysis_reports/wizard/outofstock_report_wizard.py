# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
from odoo.tools.misc import xlwt
import io
import base64
from odoo.exceptions import UserError


class Inventory_outofstock_analysis_wizard(models.Model):
    _name = 'inventory.outofstock.report.wiz'
    _description = 'Inventory Out of Stock Analysis Report'

    from_date = fields.Date('From Date')
    to_date = fields.Date('To Date')
    company_ids = fields.Many2many("res.company", string="Company")
    stock_days = fields.Integer("Next Number of Days Inventory")
    category_ids = fields.Many2many(
        "product.category", string="Product Category")
    product_ids = fields.Many2many("product.product", string="Product")
    warehouse_ids = fields.Many2many("stock.warehouse", string="Warehouse")

    @api.onchange('from_date', 'to_date', 'company_ids', 'stock_days', 'category_ids', 'product_ids', 'warehouse_ids')
    def onchange_data_set_company_domain(self):
        for rec in self:
            return {'domain': {'company_ids': [('id', 'in', self.env.user.company_ids.ids)]}}

    def print_inventory_outofstock_report(self):
        if self.to_date or self.from_date:
            if self.to_date <= self.from_date:
                raise UserError(_('End date should be greater than start date.'))

        filename = 'Inventory Out of Stock Report' + '.xls'
        workbook = xlwt.Workbook()

        worksheet = workbook.add_sheet('Inventory Out of Stock Report')
        font = xlwt.Font()
        font.bold = True
        for_left = xlwt.easyxf(
            "font: bold 1, color black; borders: top double, bottom double, left double, right double; align: horiz left")
        for_left_not_bold = xlwt.easyxf(
            "font: color black; align: horiz left", num_format_str='0.00')
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
        worksheet.col(8).width = 4000
        worksheet.col(9).width = 4000
        worksheet.col(10).width = 4000
        worksheet.col(11).width = 4000
        worksheet.col(12).width = 4000
        worksheet.col(13).width = 4000
        worksheet.col(14).width = 4000
        worksheet.col(15).width = 4000
        worksheet.col(16).width = 4000

        worksheet.write_merge(
            0, 0, 0, 5, 'Inventory Out of Stock Report', GREEN_TABLE_HEADER)
        row = 1
        col = 0
        worksheet.write(row, col, 'Company' or '', for_left)
        col = 1
        for i in self.company_ids:
            company = []
            company.append(i.name)
            worksheet.write(row, col, company or '', for_left_not_bold)
            col += 1
        row = 2
        col = 0
        worksheet.write(row, col, 'Warehouse' or '', for_left)
        col = 1
        for i in self.warehouse_ids:
            warehouse = []
            warehouse.append(i.name)
            worksheet.write(row, col, warehouse or '', for_left_not_bold)
            col += 1
        row = 3
        worksheet.write(row, 0, 'Stock Analysis For Next' or '', for_left)
        worksheet.write(row, 1, self.stock_days or '0', for_left)
        row = 4
        worksheet.write(row, 0, 'Report start date' or '', for_left)
        worksheet.write(row, 1, self.from_date.strftime(
            '%d-%m-%Y') or '', for_left)
        row = 5
        worksheet.write(row, 0, 'Report end date' or '', for_left)
        worksheet.write(row, 1, self.to_date.strftime(
            '%d-%m-%Y') or '', for_left)

        row = 6

        worksheet.write(row, 0, 'Product Name' or '', for_left)
        worksheet.write(row, 1, 'Category' or '', for_left)
        worksheet.write(row, 2, 'Current Stock' or '', for_left)
        worksheet.write(row, 3, 'Outgoing ' or '', for_left)
        worksheet.write(row, 4, 'Incoming' or '', for_left)
        worksheet.write(row, 5, 'Virtual Stock' or '', for_left)
        worksheet.write(row, 6, 'Sales' or '', for_left)
        worksheet.write(row, 7, 'ADS' or '', for_left)
        worksheet.write(row, 8, 'Demanded Qty' or '', for_left)
        worksheet.write(row, 9, 'In Stock Days' or '', for_left)
        worksheet.write(row, 10, 'OutOfStock days' or '', for_left)
        worksheet.write(row, 11, 'OutOfStock Ratio' or '', for_left)
        worksheet.write(row, 12, 'Cost Price' or '', for_left)
        worksheet.write(row, 13, 'OutOfStock Qty ' or '', for_left)
        worksheet.write(row, 14, 'OutOfStock value ' or '', for_left)
        worksheet.write(row, 15, 'OutOfStock Qty (%) ' or '', for_left)
        worksheet.write(row, 16, 'OutOfStock Value(%)' or '', for_left)
        worksheet.write(row, 17, 'Turnover Ratio(%)' or '', for_left)
        worksheet.write(row, 18, 'FSN Classification(%)' or '', for_left)

        product_ids = self.env['product.product']

        if self.category_ids:
            product_ids = self.env['product.product'].search(
                [('categ_id', 'in', self.category_ids.ids)])

        if self.product_ids:
            product_ids = self.product_ids

        if not product_ids:
            product_ids = self.env['product.product'].search([])

        rows = 7
        sr_no = 0

        total_outofstock_qty = 0.0
        total_outofstock_value = 0.0
        for product_id in product_ids:
            average = 0.0
            turnover = 0.0
            fsn_type = ''
            ads = 0.0
            demanded = 0.0
            in_stock_days = 0.0
            outofstock_days = 0.0
            outofstock_ratio = 0.0
            outofstock_qty = 0.0
            outofstock_value = 0.0
            outofstock_qty_per = 0.0
            outofstock_value_per = 0.0

            domain = [('product_id', '=', product_id.id)]

            location_domain = [('usage', 'in', ['internal'])]
            if self.company_ids:
                domain += [('company_id', 'in', self.company_ids.ids)]
                location_domain += [('company_id', 'in', self.company_ids.ids)]

            location_ids = self.env['stock.location']

            warehouse_data = self.warehouse_ids

            if not warehouse_data:
                warehouse_domain = []
                if self.company_ids:
                    warehouse_domain += [('company_id',
                                          'in', self.company_ids.ids)]
                warehouse_data = self.env['stock.warehouse'].sudo().search(
                    warehouse_domain)

            location_ids = warehouse_data.mapped('lot_stock_id')
            location_ids += location_ids.mapped('child_ids')

            if not location_ids:
                location_ids = self.env['stock.location'].search(
                    location_domain)

            domain += [('location_dest_id', 'in', location_ids.ids)]
            domain += [('state', '=', 'done')]

            date_start = self.from_date
            date_end = self.to_date

            domain += [('date', '>=', date_start), ('date', '<=', date_end)]
            product_qty = self.env['stock.move.line'].search(domain)

            avaialable_qty = sum(product_qty.mapped('quantity'))

            if product_id.sales_count and product_id.virtual_available:
                ads = product_id.sales_count/product_id.virtual_available
            if ads and self.stock_days:
                demanded = self.stock_days*ads
            if product_id.virtual_available and ads:
                in_stock_days = product_id.virtual_available/ads
            else:
                in_stock_days = 0

            if in_stock_days:
                outofstock_days = 0
            else:
                outofstock_days = self.stock_days

            if outofstock_days and self.stock_days:
                outofstock_ratio = outofstock_days*self.stock_days

            if demanded and product_id.virtual_available:
                outofstock_qty = demanded-product_id.virtual_available

            if product_id.standard_price and outofstock_qty:
                outofstock_value = product_id.standard_price*outofstock_qty
            if outofstock_qty:
                total_outofstock_qty += outofstock_qty
            if outofstock_value:
                total_outofstock_value += outofstock_value
            if outofstock_qty and total_outofstock_qty:
                outofstock_qty_per = outofstock_qty/total_outofstock_qty
            if outofstock_value and outofstock_qty_per:
                outofstock_value_per = outofstock_value/outofstock_qty_per

            opening_qty = 0.0
            closing_qty = 0.0
            for qty in product_qty:
                if product_id.id == qty.product_id.id:
                    if str(qty.date.strftime("%m-%d-%y")) <= str(self.from_date.strftime("%m-%d-%y")):
                        if qty.location_dest_id in location_ids:
                            opening_qty += qty.quantity
                        if qty.location_id in location_ids:
                            opening_qty = opening_qty-qty.quantity
                    if str(qty.date.strftime("%m-%d-%y")) <= str(self.to_date.strftime("%m-%d-%y")):
                        if qty.location_dest_id in location_ids:
                            closing_qty += qty.quantity
                        if qty.location_id in location_ids:
                            closing_qty = closing_qty-qty.quantity

            if opening_qty or closing_qty:
                average = (opening_qty + closing_qty)/2
            else:
                average = 0
            if product_id.sales_count and average:
                turnover = product_id.sales_count/average

            else:
                turnover = 0.0

            if turnover > 3:
                fsn_type = 'Fast Moving'
            if turnover >= 1 and turnover <= 3:
                fsn_type = 'Slow Moving'
            if turnover < 1:
                fsn_type = 'Non Moving'

            sr_no += 1
            worksheet.write(rows, 0, product_id.name_get()[
                            0][1] or '', for_left_not_bold)
            worksheet.write(rows, 1, product_id.categ_id.name_get()[
                            0][1] or '', for_left_not_bold)
            worksheet.write(
                rows, 2, avaialable_qty or '0', for_left_not_bold)
            worksheet.write(
                rows, 3, product_id.outgoing_qty or '0', for_left_not_bold)
            worksheet.write(
                rows, 4, product_id.incoming_qty or '0', for_left_not_bold)
            worksheet.write(
                rows, 5, product_id.virtual_available or '0', for_left_not_bold)
            worksheet.write(
                rows, 6, product_id.sales_count or '0', for_left_not_bold)
            worksheet.write(rows, 7, ads or '0',
                            for_left_not_bold)
            worksheet.write(
                rows, 8, demanded or '0', for_left_not_bold)
            worksheet.write(
                rows, 9, in_stock_days or '0', for_left_not_bold)
            worksheet.write(
                rows, 10, outofstock_days or '0', for_left_not_bold)
            worksheet.write(
                rows, 11, outofstock_ratio or '0', for_left_not_bold)
            worksheet.write(
                rows, 12, product_id.standard_price or '0', for_left_not_bold)
            worksheet.write(
                rows, 13, outofstock_qty or '0', for_left_not_bold)
            worksheet.write(
                rows, 14, outofstock_value or '0', for_left_not_bold)
            worksheet.write(
                rows, 15, outofstock_qty_per or '0', for_left_not_bold)
            worksheet.write(
                rows, 16, outofstock_value_per or '0', for_left_not_bold)
            worksheet.write(
                rows, 17, turnover or '', for_left_not_bold)
            worksheet.write(
                rows, 18, fsn_type or '', for_left_not_bold)
            rows += 1

        fp = io.BytesIO()
        workbook.save(fp)
        outofstock_id = self.env['inventory.outofstock.extended'].create(
            {'excel_file': base64.encodebytes(fp.getvalue()), 'file_name': filename})
        fp.close()

        return {
            'view_mode': 'form',
            'res_id': outofstock_id.id,
            'res_model': 'inventory.outofstock.extended',
            'type': 'ir.actions.act_window',
            'context': self._context,
            'target': 'new',
        }

    def tree_graph_report_view(self):

        if self.to_date or self.from_date:
            if self.to_date <= self.from_date:
                raise UserError(_('End date should be greater than start date.'))

        product_ids = self.env['product.product']

        if self.category_ids:
            product_ids = self.env['product.product'].search(
                [('categ_id', 'in', self.category_ids.ids)])

        if self.product_ids:
            product_ids = self.product_ids

        if not product_ids:
            product_ids = self.env['product.product'].search([])

        total_outofstock_qty = 0.0
        total_outofstock_value = 0.0
        OutofstockObj = self.env['inventory.outofstock.extended']
        record_set = OutofstockObj.search([])
        record_set.unlink()
        for product_id in product_ids:
            average = 0.0
            turnover = 0.0
            fsn_type = ''
            ads = 0.0
            demanded = 0.0
            in_stock_days = 0.0
            outofstock_days = 0.0
            outofstock_ratio = 0.0
            outofstock_qty = 0.0
            outofstock_value = 0.0
            outofstock_qty_per = 0.0
            outofstock_value_per = 0.0

            domain = [('product_id', '=', product_id.id)]

            location_domain = [('usage', 'in', ['internal'])]
            if self.company_ids:
                domain += [('company_id', 'in', self.company_ids.ids)]
                location_domain += [('company_id', 'in', self.company_ids.ids)]

            location_ids = self.env['stock.location']

            warehouse_data = self.warehouse_ids
            warehouse = self.env['stock.warehouse'].sudo().search([], limit=1)
            if not warehouse_data:
                warehouse_domain = []
                if self.company_ids:
                    warehouse_domain += [('company_id',
                                          'in', self.company_ids.ids)]
                warehouse_data = self.env['stock.warehouse'].sudo().search(
                    warehouse_domain)
                warehouse = warehouse_data[0]
            location_ids = warehouse_data.mapped('lot_stock_id')
            location_ids += location_ids.mapped('child_ids')

            if not location_ids:
                location_ids = self.env['stock.location'].search(
                    location_domain)

            domain += [('location_dest_id', 'in', location_ids.ids)]
            domain += [('state', '=', 'done')]

            date_start = self.from_date
            date_end = self.to_date

            domain += [('date', '>=', date_start), ('date', '<=', date_end)]
            product_qty = self.env['stock.move.line'].search(domain)

            available_quantity = sum(product_qty.mapped('quantity'))

            if product_id.sales_count and product_id.virtual_available:
                ads = product_id.sales_count/product_id.virtual_available
            if ads and self.stock_days:
                demanded = self.stock_days*ads
            if product_id.virtual_available and ads:
                in_stock_days = product_id.virtual_available/ads
            else:
                in_stock_days = 0
            if in_stock_days:
                outofstock_days = 0
            else:
                outofstock_days = self.stock_days

            if outofstock_days and self.stock_days:
                outofstock_ratio = outofstock_days*self.stock_days
            if demanded and product_id.virtual_available:
                outofstock_qty = demanded-product_id.virtual_available
            if product_id.standard_price and outofstock_qty:
                outofstock_value = product_id.standard_price*outofstock_qty
            if outofstock_qty:
                total_outofstock_qty += outofstock_qty
            if outofstock_value:
                total_outofstock_value += outofstock_value
            if outofstock_qty and total_outofstock_qty:
                outofstock_qty_per = outofstock_qty/total_outofstock_qty
            if outofstock_value and outofstock_qty_per:
                outofstock_value_per = outofstock_value/outofstock_qty_per

            opening_qty = 0.0
            closing_qty = 0.0
            for qty in product_qty:
                if product_id.id == qty.product_id.id:
                    if str(qty.date.strftime("%m-%d-%y")) <= str(self.from_date.strftime("%m-%d-%y")):
                        if qty.location_dest_id in location_ids:
                            opening_qty += qty.quantity
                        if qty.location_id in location_ids:
                            opening_qty = opening_qty-qty.quantity
                    if str(qty.date.strftime("%m-%d-%y")) <= str(self.to_date.strftime("%m-%d-%y")):
                        if qty.location_dest_id in location_ids:
                            closing_qty += qty.quantity
                        if qty.location_id in location_ids:
                            closing_qty = closing_qty-qty.quantity

            if opening_qty or closing_qty:
                average = (opening_qty + closing_qty)/2
            else:
                average = 0
            if product_id.sales_count and average:
                turnover = product_id.sales_count/average
            else:
                turnover = 0.0

            if turnover > 3:
                fsn_type = 'Fast Moving'
            if turnover >= 1 and turnover <= 3:
                fsn_type = 'Slow Moving'
            if turnover < 1:
                fsn_type = 'Non Moving'

            if self.company_ids:
                company_ids = self.company_ids
            else:
                company_ids = self.env['res.company'].sudo().search([])

            if self.warehouse_ids:
                warehouse_ids = self.warehouse_ids
            else:
                warehouse_ids = self.env['stock.warehouse'].sudo().search([])

            dispaly_product_id = OutofstockObj.create({
                'products': product_id.id,
                'product_category': product_id.categ_id.id,
                # 'company': warehouse.company_id.id,
                # 'warehouse': warehouse.id,
                'company_ids': company_ids.ids,
                'warehouse_ids': warehouse_ids.ids,
                'qty_demanded': demanded,
                'stock_available': available_quantity,
                'sales': product_id.sales_count,
                'turnover': turnover,
                'days_outofstock': outofstock_days,
                'instock_days': in_stock_days,
                'stock_forecasted': product_id.virtual_available,
                'ratio_outofstock': outofstock_ratio,
                'ads': ads,
                'movement_fns_type': fsn_type,
                'qty_incoming': product_id.incoming_qty,
                'qty_outgoing': product_id.outgoing_qty,
                'cost': product_id.standard_price,
                'qty_outofstock': outofstock_qty,
                'value_outofstock': outofstock_value,
                'qty_per_outofstock': abs(outofstock_qty_per),
                'value_per_outofstock': outofstock_value_per,
            })

        display = []
        graph_id = self.env.ref(
            'bi_all_inventory_analysis_reports.inventory_outofstock_extended_report_graph').id
        tree_id = self.env.ref(
            'bi_all_inventory_analysis_reports.inventory_outofstock_extended_report_tree').id
        graph_first = self.env.context.get('report_graph', False)

        if graph_first:
            display.append((graph_id, 'graph'))
            display.append((tree_id, 'tree'))
        else:
            display.append((tree_id, 'tree'))
            display.append((graph_id, 'graph'))
        return {
            'name': _('Warehouse Out of Stock Analysis Report'),
            'res_model': 'inventory.outofstock.extended',
            'view_mode': 'tree',
            'type': 'ir.actions.act_window',
            'views': display,
        }


class Inventory_OutofStock_analysis_Extended(models.TransientModel):
    _name = 'inventory.outofstock.extended'
    _description = "Stock Out Of Stock Excel Extended"

    excel_file = fields.Binary('Download Report :- ')
    file_name = fields.Char('Excel File', size=64)

    products = fields.Many2one("product.product", "Product")
    product_category = fields.Many2one("product.category", "Category")
    # warehouse = fields.Many2one("stock.warehouse")
    # company = fields.Many2one("res.company", "Company")
    company_ids = fields.Many2many("res.company", 'rel_company_outstock', 'company_id', 'outstock_id', string="Company")
    warehouse_ids = fields.Many2many("stock.warehouse", 'rel_warehouse_outstock', 'warehouse_id', 'outstock_id', string="Warehouse")
    wizard_id = fields.Many2one("inventory.outofstock.report.wiz")
    sales = fields.Float("Sales")
    ads = fields.Float("ADS")
    qty_demanded = fields.Float("Demanded Qty")
    stock_available = fields.Float("Current Stock")
    qty_incoming = fields.Float("Incoming")
    qty_outgoing = fields.Float("Outgoing")
    stock_forecasted = fields.Float("Forecasted Stock")
    ratio_outofstock = fields.Float("OutOfStock Ratio")
    instock_days = fields.Float("In Stock Days")
    days_outofstock = fields.Float("OutOfStock Days")
    cost = fields.Float("Cost Price")
    qty_outofstock = fields.Float("OutOfstock Qty")
    value_outofstock = fields.Float("OutOfstock Value")
    qty_per_outofstock = fields.Float("OutOfstock Qty (%)")
    value_per_outofstock = fields.Float("OutOfstock Value (%)")
    turnover = fields.Float("Turnover Ratio")
    movement_fns_type = fields.Char("Classification For FSN")
