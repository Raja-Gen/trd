# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _

from odoo.tools.misc import xlwt
import io
import base64

from odoo.exceptions import UserError, ValidationError


class Inventory_OverStock_analysis_wizard(models.Model):
    _name = 'inventory.overstock.report.wiz'
    _description = 'Inventory OverStock Analysis Report'

    from_date = fields.Date('From Date')
    to_date = fields.Date('To Date')
    company_ids = fields.Many2many("res.company", string="Company")
    stock_days = fields.Integer("Next Number of Days Inventory")
    category_ids = fields.Many2many("product.category", string="Product Category")
    product_ids = fields.Many2many("product.product", string="Product")
    warehouse_ids = fields.Many2many("stock.warehouse", string="Warehouse")

    @api.constrains('from_date', 'to_date')
    def validate_end_date(self):
        for record in self:
            if record.from_date and record.to_date and record.from_date >= record.to_date:
                raise ValidationError(_("Oops! 'To Date' is small to the 'From Date'."))

    def print_inventory_overstock_report(self):

        filename = 'Inventory Overstock Report' + '.xls'
        workbook = xlwt.Workbook()

        worksheet = workbook.add_sheet('Inventory Overstock Report')
        font = xlwt.Font()
        font.bold = True
        for_left = xlwt.easyxf(
            "font: bold 1, color black; borders: top double, bottom double, left double, right double; align: horiz left")
        for_left_not_bold = xlwt.easyxf("font: color black; align: horiz left", num_format_str='0.00')
        for_center_bold = xlwt.easyxf(
            "font: bold 1, color black; align: horiz center")
        GREEN_TABLE_HEADER = xlwt.easyxf(
            'font: bold 1, name Tahoma, height 250;'
            'align: vertical center, horizontal center, wrap on;'
            'borders: top double, bottom double, left double, right double;'
        )
        style = xlwt.easyxf(
            'font:height 400, bold True, name Arial; align: horiz center, vert center;borders: top medium,right medium,bottom medium,left medium')

        alignment = xlwt.Alignment()
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
            0, 0, 0, 5, 'Inventory Overstock Report', GREEN_TABLE_HEADER)

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
        worksheet.write(row, 1, self.stock_days or '', for_left)
        row = 4
        worksheet.write(row, 0, 'Report start date' or '', for_left)
        worksheet.write(row, 1, self.from_date.strftime('%d-%m-%Y') or '', for_left)
        row = 5
        worksheet.write(row, 0, 'Report end date' or '', for_left)
        worksheet.write(row, 1, self.to_date.strftime('%d-%m-%Y') or '', for_left)

        row = 6

        worksheet.write(row, 0, 'Product Name' or '', for_left)
        worksheet.write(row, 1, 'Category' or '', for_left)
        worksheet.write(row, 2, 'Sales' or '', for_left)
        worksheet.write(row, 3, 'ADS ' or '', for_left)
        worksheet.write(row, 4, 'Current Stock ' or '', for_left)
        worksheet.write(row, 5, 'Outgoing ' or '', for_left)
        worksheet.write(row, 6, 'Incoming' or '', for_left)
        worksheet.write(row, 7, 'Virtual Stock' or '', for_left)
        worksheet.write(row, 8, 'Demanded Qty' or '', for_left)
        worksheet.write(row, 9, 'Coverage days' or '', for_left)
        worksheet.write(row, 10, 'OverStock Qty' or '', for_left)
        worksheet.write(row, 11, 'OverStock Value' or '', for_left)
        worksheet.write(row, 12, 'Turnover Ratio' or '', for_left)
        worksheet.write(row, 13, 'FSN Classification(%)' or '', for_left)
        worksheet.write(row, 14, 'OverStock Qty(%)' or '', for_left)
        worksheet.write(row, 15, 'OverStock Value(%)' or '', for_left)
        worksheet.write(row, 16, 'Last PO Date' or '', for_left)
        worksheet.write(row, 17, 'Last PO Qty' or '', for_left)
        worksheet.write(row, 18, 'Last PO Price' or '', for_left)
        worksheet.write(row, 19, 'Currency' or '', for_left)
        worksheet.write(row, 20, 'Vendor' or '', for_left)

        if self.category_ids and not self.product_ids:
            product_category = self.env['product.product'].search([('categ_id', 'in', self.category_ids.ids)])

        elif self.category_ids and self.product_ids:
            product_category = self.env['product.product'].search(
                [('categ_id', 'in', self.category_ids.ids), ('id', 'in', self.product_ids.ids)])

        elif not self.category_ids and self.product_ids:
            product_category = self.env['product.product'].search([('id', 'in', self.product_ids.ids)])

        else:
            product_category = self.env['product.product'].search([])

        stock_data = self.env['stock.quant'].search([])
        if self.warehouse_ids and not self.company_ids:
            warehouse_data = self.env['stock.warehouse'].search([('id', 'in', self.warehouse_ids.ids)])
        elif not self.warehouse_ids and self.company_ids:
            warehouse_data = self.env['stock.warehouse'].search([('company_id', 'in', self.company_ids.ids)])
        elif self.warehouse_ids and self.company_ids:
            warehouse_data = self.env['stock.warehouse'].search(
                [('id', 'in', self.warehouse_ids.ids), ('company_id', 'in', self.company_ids.ids)])

        else:
            warehouse_data = self.env['stock.warehouse'].search([])
        sale_report = self.env['sale.report'].search([])
        product_qty = self.env['stock.move.line'].search(
            [('create_date', '>=', self.from_date), ('create_date', '<=', self.to_date)])
        rows = 7
        sr_no = 0

        fsn_type = ''
        total_overstock_qty = 0.0
        total_overstock_value = 0.0
        for rec1 in product_category:
            purchase_data = self.env['purchase.order.line'].search([('product_id.id', '=', rec1.id)], order='id desc',
                                                                   limit=1)
            ads = 0.0
            demanded = 0.0
            coverage_days = 0.0
            overstock_qty = 0.0
            overstock_value = 0.0
            overstock_qty_per = 0.0
            overstock_value_per = 0.0
            turnover = 0.0
            average = 0.0
            virtual_stock = 0.0

            for record in stock_data:
                for warehouse in warehouse_data:

                    if rec1.id == record.product_id.id:
                        data_line = sale_report.filtered(lambda
                                                             l: l.date.date() >= self.from_date and l.date.date() <= self.to_date and l.state in [
                            'sale', 'done'])
                        total = 0
                        for rec in data_line:
                            if rec.product_id.id == record.product_id.id:
                                total += rec.product_uom_qty

                        location_ids = warehouse.lot_stock_id + warehouse.lot_stock_id.child_ids
                        if record.location_id in location_ids:

                            if rec1.sales_count and rec1.virtual_available:
                                ads = rec1.sales_count / rec1.virtual_available
                            if ads and self.stock_days:
                                demanded = self.stock_days * ads
                            if rec1.virtual_available and ads:
                                coverage_days = rec1.virtual_available / ads
                            if rec1.virtual_available:
                                overstock_qty = rec1.virtual_available - demanded
                            if rec1.standard_price and overstock_qty:
                                overstock_value = rec1.standard_price * overstock_qty
                            if overstock_qty:
                                total_overstock_qty += overstock_qty
                            if overstock_value:
                                total_overstock_value += overstock_value
                            if total_overstock_qty and overstock_qty:
                                overstock_qty_per = (overstock_qty / total_overstock_qty) * 100
                            if overstock_value and total_overstock_value:
                                overstock_value_per = (overstock_value / total_overstock_value) * 100

                            opening_qty = 0.0
                            closing_qty = 0.0
                            for qty in product_qty:
                                if rec1.id == qty.product_id.id:
                                    if str(qty.date.strftime("%m-%d-%y")) <= str(self.from_date.strftime("%m-%d-%y")):
                                        if qty.location_dest_id in location_ids:
                                            opening_qty += qty.quantity
                                        if qty.location_id in location_ids:
                                            opening_qty = opening_qty - qty.quantity
                                    if str(qty.date.strftime("%m-%d-%y")) <= str(self.to_date.strftime("%m-%d-%y")):
                                        if qty.location_dest_id in location_ids:
                                            closing_qty += qty.quantity
                                        if qty.location_id in location_ids:
                                            closing_qty = closing_qty - qty.quantity

                            if opening_qty or closing_qty:
                                average = (opening_qty + closing_qty) / 2
                            else:
                                average = 0

                            po_qty = 0.0
                            po_price = 0.0
                            po_date = ''
                            currency = ''
                            vendor = ''

                            for rec in purchase_data:
                                if rec1.id == rec.product_id.id:
                                    po_qty = rec.product_qty
                                    po_date = str(rec.date_planned.strftime("%d-%m-%y"))
                                    currency = rec.currency_id.name
                                    vendor = rec.partner_id.name
                            if po_qty:
                                po_price = rec1.standard_price

                            if rec1.sales_count and average:
                                turnover = rec1.sales_count / average
                            else:
                                turnover = 0.0

                            if turnover > 3:
                                fsn_type = 'Fast Moving'
                            if turnover >= 1 and turnover <= 3:
                                fsn_type = 'Slow Moving'
                            if turnover < 1:
                                fsn_type = 'Non Moving'

                            sr_no += 1
                            worksheet.write(rows, 0, record.product_id.name_get()[0][1] or '', for_left_not_bold)
                            worksheet.write(rows, 1, rec1.categ_id.name_get()[0][1] or '', for_left_not_bold)
                            worksheet.write(rows, 2, total or '0', for_left_not_bold)
                            worksheet.write(rows, 3, ads or '0', for_left_not_bold)
                            worksheet.write(rows, 4, record.available_quantity or '0', for_left_not_bold)
                            worksheet.write(rows, 5, rec1.outgoing_qty or '0', for_left_not_bold)
                            worksheet.write(rows, 6, rec1.incoming_qty or '0', for_left_not_bold)
                            worksheet.write(rows, 7, rec1.virtual_available or '0', for_left_not_bold)
                            worksheet.write(rows, 8, demanded or '0', for_left_not_bold)
                            worksheet.write(rows, 9, coverage_days or '0', for_left_not_bold)
                            worksheet.write(rows, 10, overstock_qty or '0', for_left_not_bold)
                            worksheet.write(rows, 11, overstock_value or '0', for_left_not_bold)
                            worksheet.write(rows, 12, turnover or '0', for_left_not_bold)
                            worksheet.write(rows, 13, fsn_type or '0', for_left_not_bold)
                            worksheet.write(rows, 14, overstock_qty_per or '0', for_left_not_bold)
                            worksheet.write(rows, 15, overstock_value_per or '0', for_left_not_bold)
                            worksheet.write(rows, 16, po_date or '', for_left_not_bold)
                            worksheet.write(rows, 17, po_qty or '0', for_left_not_bold)
                            worksheet.write(rows, 18, po_price or '0', for_left_not_bold)
                            worksheet.write(rows, 19, currency or '', for_left_not_bold)
                            worksheet.write(rows, 20, vendor or '', for_left_not_bold)
                            rows += 1

        fp = io.BytesIO()
        workbook.save(fp)
        overstock_id = self.env['inventory.overstock.extended'].create(
            {'excel_file': base64.b64encode(fp.getvalue()), 'file_name': filename})
        fp.close()

        return {
            'view_mode': 'form',
            'res_id': overstock_id.id,
            'res_model': 'inventory.overstock.extended',
            'type': 'ir.actions.act_window',
            'context': self._context,
            'target': 'new',
        }

    def tree_graph_report_view(self):
        if self.category_ids and not self.product_ids:
            product_category = self.env['product.product'].search([('categ_id', 'in', self.category_ids.ids)])

        elif self.category_ids and self.product_ids:
            product_category = self.env['product.product'].search(
                [('categ_id', 'in', self.category_ids.ids), ('id', 'in', self.product_ids.ids)])

        elif not self.category_ids and self.product_ids:
            product_category = self.env['product.product'].search([('id', 'in', self.product_ids.ids)])

        else:
            product_category = self.env['product.product'].search([])

        stock_data = self.env['stock.quant'].search([])
        if self.warehouse_ids and not self.company_ids:
            warehouse_data = self.env['stock.warehouse'].search([('id', 'in', self.warehouse_ids.ids)])
        elif not self.warehouse_ids and self.company_ids:
            warehouse_data = self.env['stock.warehouse'].search([('company_id', 'in', self.company_ids.ids)])
        elif self.warehouse_ids and self.company_ids:
            warehouse_data = self.env['stock.warehouse'].search(
                [('id', 'in', self.warehouse_ids.ids), ('company_id', 'in', self.company_ids.ids)])

        else:
            warehouse_data = self.env['stock.warehouse'].search([])
        sale_report = self.env['sale.report'].search([])
        product_qty = self.env['stock.move.line'].search(
            [('create_date', '>=', self.from_date), ('create_date', '<=', self.to_date)])

        total_overstock_qty = 0.0
        total_overstock_value = 0.0
        record_set = self.env['inventory.overstock.extended'].search([])
        record_set.unlink()
        for data in product_category:
            purchase_data = self.env['purchase.order.line'].search([('product_id.id', '=', data.id)], order='id desc',
                                                                   limit=1)
            inv_obj = self.env['inventory.overstock.extended']
            self.ensure_one()
            ads = 0.0
            demanded = 0.0
            coverage_days = 0.0
            overstock_qty = 0.0
            overstock_value = 0.0
            overstock_qty_per = 0.0
            overstock_value_per = 0.0
            turnover = 0.0
            average = 0.0
            virtual_stock = 0.0

            for record in stock_data:
                for warehouse in warehouse_data:

                    if data.id == record.product_id.id:

                        data_line = sale_report.filtered(lambda
                                                             l: l.date.date() >= self.from_date and l.date.date() <= self.to_date and l.state in [
                            'sale', 'done'])
                        total = 0
                        for rec in data_line:
                            if rec.product_id.id == record.product_id.id:
                                total += rec.product_uom_qty

                        location_ids = warehouse.lot_stock_id + warehouse.lot_stock_id.child_ids
                        if record.location_id in location_ids:

                            if data.sales_count and data.virtual_available:
                                ads = data.sales_count / data.virtual_available
                            if ads and self.stock_days:
                                demanded = self.stock_days * ads
                            if data.virtual_available and ads:
                                coverage_days = data.virtual_available / ads
                            if data.virtual_available:
                                overstock_qty = data.virtual_available - demanded
                            if data.standard_price and overstock_qty:
                                overstock_value = data.standard_price * overstock_qty
                            if overstock_qty:
                                total_overstock_qty += overstock_qty
                            if overstock_value:
                                total_overstock_value += overstock_value
                            if total_overstock_qty and overstock_qty:
                                overstock_qty_per = (overstock_qty / total_overstock_qty) * 100
                            if overstock_value and total_overstock_value:
                                overstock_value_per = (overstock_value / total_overstock_value) * 100

                            opening_qty = 0.0
                            closing_qty = 0.0
                            for qty in product_qty:
                                if data.id == qty.product_id.id:
                                    if str(qty.date.strftime("%m-%d-%y")) <= str(self.from_date.strftime("%m-%d-%y")):
                                        if qty.location_dest_id in location_ids:
                                            opening_qty += qty.quantity
                                        if qty.location_id in location_ids:
                                            opening_qty = opening_qty - qty.quantity
                                    if str(qty.date.strftime("%m-%d-%y")) <= str(self.to_date.strftime("%m-%d-%y")):
                                        if qty.location_dest_id in location_ids:
                                            closing_qty += qty.quantity
                                        if qty.location_id in location_ids:
                                            closing_qty = closing_qty - qty.quantity

                            if opening_qty or closing_qty:
                                average = (opening_qty + closing_qty) / 2
                            else:
                                average = 0
                            po_qty = 0.0
                            po_price = 0.0
                            po_date = ''
                            currency = ''
                            vendor = ''

                            for rec in purchase_data:
                                if data.id == rec.product_id.id:
                                    po_qty = rec.product_qty
                                    po_date = str(rec.date_planned.strftime("%d-%m-%y"))
                                    currency = rec.currency_id.name
                                    vendor = rec.partner_id.name
                            if po_qty:
                                po_price = data.standard_price

                            if data.sales_count and average:
                                turnover = data.sales_count / average
                            else:
                                turnover = 0.0

                            if turnover > 3:
                                fsn_type = 'Fast Moving'
                            if turnover >= 1 and turnover <= 3:
                                fsn_type = 'Slow Moving'
                            if turnover < 1:
                                fsn_type = 'Non Moving'

                            dispaly_data = inv_obj.create({
                                'products': record.product_id.id,
                                'product_category': data.categ_id.id,
                                'company': warehouse.company_id.id,
                                'warehouse': warehouse.id,
                                'qty_demanded': demanded,
                                'stock_available': record.available_quantity,
                                'sales': total,
                                'turnover': turnover,
                                'days_coverage': coverage_days,
                                'stock_forecasted': data.virtual_available,
                                'purchase_last_qty': po_qty,
                                'purchase_last_price': po_price,
                                'purchase_last_date': po_date,
                                'name_of_currency': currency,
                                'name_of_vendor': vendor,
                                'ads': ads,
                                'movement_fns_type': fsn_type,
                                'qty_incoming': data.incoming_qty,
                                'qty_outgoing': data.outgoing_qty,
                                'qty_overstock': overstock_qty,
                                'value_OverStock': overstock_value,
                                'qty_per_OverStock': abs(overstock_qty_per),
                                'value_per_OverStock': overstock_value_per,

                            })

        display = []
        graph_id = self.env.ref('bi_overstock_report.inventory_overstock_extended_report_graph').id
        tree_id = self.env.ref('bi_overstock_report.inventory_overstock_extended_report_tree').id
        graph_first = self.env.context.get('report_graph', False)

        if graph_first:
            display.append((graph_id, 'graph'))
            display.append((tree_id, 'tree'))
        else:
            display.append((tree_id, 'tree'))
            display.append((graph_id, 'graph'))
        return {
            'name': _('Warehouse Overstock Analysis Report'),
            'res_model': 'inventory.overstock.extended',
            'view_mode': 'tree',
            'type': 'ir.actions.act_window',
            'views': display,
        }


class Inventory_OverStock_analysis_Extended(models.TransientModel):
    _name = 'inventory.overstock.extended'
    _description = "Stock OverStock Excel Extended"

    excel_file = fields.Binary('Download Report :- ')
    file_name = fields.Char('Excel File', size=64)

    products = fields.Many2one("product.product", "Product")
    product_category = fields.Many2one("product.category", "Category")
    warehouse = fields.Many2one("stock.warehouse")
    company = fields.Many2one("res.company", "Company")
    wizard_id = fields.Many2one("inventory.overstock.report.wiz")
    sales = fields.Float("Sales")
    ads = fields.Float("ADS")
    qty_demanded = fields.Float("Demanded Qty")
    stock_available = fields.Float("Current Stock")
    qty_incoming = fields.Float("Incoming")
    qty_outgoing = fields.Float("Outgoing")
    stock_forecasted = fields.Float("Forecasted Stock")
    qty_overstock = fields.Float("OverStock Qty")
    days_coverage = fields.Float("Coverage Days")
    value_OverStock = fields.Float("OverStock Value")
    qty_per_OverStock = fields.Float("OverStock Qty (%)")
    value_per_OverStock = fields.Float("OverStock Value (%)")
    turnover = fields.Float("Turnover Ratio")
    movement_fns_type = fields.Char("Classification For FSN")
    purchase_last_date = fields.Char("Last PO Date")
    purchase_last_qty = fields.Float("Purchase Qty")
    purchase_last_price = fields.Float("Purchase Price")
    name_of_currency = fields.Char("Currency")
    name_of_vendor = fields.Char("Vendor")
