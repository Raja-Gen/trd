# -*- coding: utf-8 -*-
# Part of BrowseInfo. See LICENSE file for full copyright and licensing details.

from odoo import fields, models, api, _
# from odoo.tools.misc import xlwt
import xlwt
import io
import base64
from odoo.exceptions import UserError


class Inventory_Turnover_analysis_wizard(models.Model):
    _name = 'inventory.turnover.report.wiz'
    _description = 'Warehouse Turnover Analysis Report'

    from_date = fields.Date('Start Date')
    to_date = fields.Date('End Date')
    company_ids = fields.Many2many("res.company", string="Companies")
    category_ids = fields.Many2many(
        "product.category", string="Product Categories")
    product_ids = fields.Many2many("product.product", string="Products")
    warehouse_ids = fields.Many2many("stock.warehouse", string="Warehouses")

    @api.onchange('from_date', 'to_date', 'company_ids', 'category_ids', 'product_ids', 'warehouse_ids')
    def onchange_data_set_company_domain(self):
        for rec in self:
            return {'domain': {'company_ids': [('id', 'in', self.env.user.company_ids.ids)]}}

    def print_inventory_turnover_report(self):

        if self.to_date or self.from_date:
            if self.to_date <= self.from_date:
                raise UserError(_('End date should be greater than start date.'))

        filename = 'Warehouse Turnover Analysis Report' + '.xls'
        workbook = xlwt.Workbook()

        worksheet = workbook.add_sheet('Warehouse Turnover Analysis Report')
        font = xlwt.Font()
        font.bold = True
        for_left = xlwt.easyxf(
            "font: bold 1, color black; borders: top double, bottom double, left double, right double; align: horiz left")
        for_left_not_bold = xlwt.easyxf(
            "font: color black; align: horiz left", num_format_str='0.00')

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
            0, 0, 0, 5, 'Warehouse Turnover Analysis Report', GREEN_TABLE_HEADER)

        row = 2

        col = 0
        worksheet.write(row, col, 'Company' or '', for_left)
        col += 1
        company = ', '.join(self.company_ids.mapped('name')
                            ) if self.company_ids else ''
        worksheet.write(row, col, company, for_left_not_bold)
        row += 1

        col = 0
        worksheet.write(row, col, 'Warehouse' or '', for_left)
        col += 1
        warehouse = ', '.join(self.warehouse_ids.mapped(
            'name')) if self.warehouse_ids else ''
        worksheet.write(row, col, warehouse, for_left_not_bold)
        row += 1

        row += 1
        worksheet.write(row, 0, 'Report start date' or '', for_left)
        worksheet.write(row, 1, self.from_date.strftime(
            '%d-%m-%Y') or '', for_left)
        row += 1
        worksheet.write(row, 0, 'Report end date' or '', for_left)
        worksheet.write(row, 1, self.to_date.strftime(
            '%d-%m-%Y') or '', for_left)

        row += 1

        worksheet.write(row, 0, 'Product Name' or '', for_left)
        worksheet.write(row, 1, 'Category' or '', for_left)
        worksheet.write(row, 2, 'Opening Stock' or '', for_left)
        worksheet.write(row, 3, 'Closing Stock' or '', for_left)
        worksheet.write(row, 4, 'Average Stock' or '', for_left)
        worksheet.write(row, 5, 'Sales' or '', for_left)
        worksheet.write(row, 6, 'Turnover Ratio' or '', for_left)

        rows = row + 1

        self._create_turnover_data()
        dispaly_data = self.env['inventory.turnover.extended'].search([])
        for record in dispaly_data:
            worksheet.write(rows, 0, record.products.display_name or '', for_left_not_bold)
            worksheet.write(rows, 1, record.product_category.display_name or '', for_left_not_bold)
            worksheet.write(
                rows, 2, record.stock_opening or '0.0', for_left_not_bold)
            worksheet.write(
                rows, 3, record.stock_closing or '0.0', for_left_not_bold)
            worksheet.write(
                rows, 4, record.stock_average or '0.0', for_left_not_bold)
            worksheet.write(rows, 5, record.sales or '0.0', for_left_not_bold)
            worksheet.write(rows, 6, record.turnover or '0.0',
                            for_left_not_bold)

            rows += 1

        fp = io.BytesIO()
        workbook.save(fp)
        turnover_id = self.env['inventory.turnover.extended'].create(
            {'excel_file': base64.encodebytes(fp.getvalue()), 'file_name': filename})
        fp.close()

        return {
            'view_mode': 'form',
            'res_id': turnover_id.id,
            'res_model': 'inventory.turnover.extended',
            'type': 'ir.actions.act_window',
            'context': self._context,
            'target': 'new',
        }

    def _create_turnover_data(self):

        product_ids = self.env['product.product']

        domain = [('type', '=', 'product')]

        if self.category_ids:
            domain += [('categ_id', 'in', self.category_ids.ids)]

        if self.product_ids:
            domain += [('id', 'in', self.product_ids.ids)]

        product_ids = self.env['product.product'].search(domain)

        OutofStockObj = self.env['inventory.turnover.extended']
        record_ids = OutofStockObj.search([])
        record_ids.unlink()

        for product_id in product_ids:
            domain = [('product_id', '=', product_id.id)]

            location_domain = [('usage', 'in', ['internal'])]
            if self.company_ids:
                domain += [('company_id', 'in', self.company_ids.ids)]
                location_domain += [('company_id', 'in', self.company_ids.ids)]

            location_ids = self.env['stock.location']
            warehouse = self.env['stock.warehouse'].sudo().search([], limit=1)
            if self.warehouse_ids:
                location_ids = self.warehouse_ids.mapped('lot_stock_id')
                location_ids += location_ids.mapped('child_ids')
                warehouse = self.warehouse_ids[0]

            if not location_ids:
                location_ids = self.env['stock.location'].search(
                    location_domain)

            domain += ['|', ('location_id', 'in', location_ids.ids),
                       ('location_dest_id', 'in', location_ids.ids)]
            domain += [('state', '=', 'done')]

            date_start = self.from_date
            date_end = self.to_date

            opening_stock_domain = domain + [('date', '<=', date_start)]
            opening_stock_data = self.env['stock.move.line'].search(
                opening_stock_domain)

            closing_stock_domain = domain + [('date', '>=', date_end)]
            closing_stock_data = self.env['stock.move.line'].search(
                closing_stock_domain)

            opening_qty = sum(opening_stock_data.filtered(lambda x: x.location_id in location_ids).mapped(
                'qty_done')) - sum(opening_stock_data.filtered(lambda x: x.location_dest_id in location_ids).mapped('qty_done'))
            closing_qty = sum(closing_stock_data.filtered(lambda x: x.location_id in location_ids).mapped(
                'qty_done')) - sum(closing_stock_data.filtered(lambda x: x.location_dest_id in location_ids).mapped('qty_done'))

            if opening_qty or closing_qty:
                average = (opening_qty + closing_qty)/2
            else:
                average = 0

            if product_id.sales_count and average:
                turnover = product_id.sales_count/average
            else:
                turnover = 0.0

            if self.company_ids:
                company_ids = self.company_ids
            else:
                company_ids = self.env['res.company'].sudo().search([])

            if self.warehouse_ids:
                warehouse_ids = self.warehouse_ids
            else:
                warehouse_ids = self.env['stock.warehouse'].sudo().search([])

            OutofStockObj.create({
                'products': product_id.id,
                'product_category': product_id.categ_id.id,
                # 'company': warehouse.company_id.id,
                # 'warehouse': warehouse.id,
                'company_ids': company_ids.ids,
                'warehouse_ids': warehouse_ids.ids,
                'stock_opening': opening_qty,
                'stock_closing': closing_qty,
                'stock_average': average,
                'sales': product_id.sales_count,
                'turnover': turnover,
            })

    def tree_graph_report_view(self):

        if self.to_date or self.from_date:
            if self.to_date <= self.from_date:
                raise UserError(_('End date should be greater than start date.'))

        self._create_turnover_data()
        display = []
        graph_id = self.env.ref(
            'bi_all_inventory_analysis_reports.inventory_turnover_extended_report_graph').id
        tree_id = self.env.ref(
            'bi_all_inventory_analysis_reports.inventory_turnover_extended_report_tree').id
        graph_first = self.env.context.get('report_graph', False)

        if graph_first:
            display.append((graph_id, 'graph'))
            display.append((tree_id, 'list'))
        else:
            display.append((tree_id, 'list'))
            display.append((graph_id, 'graph'))

        return {
            'name': _('Warehouse Turnover Ratio Analysis'),
            'res_model': 'inventory.turnover.extended',
            'view_mode': 'list',
            'type': 'ir.actions.act_window',
            'views': display,
        }


class Inventory_Turnover_analysis_Extended(models.TransientModel):
    _name = 'inventory.turnover.extended'
    _description = "inventory turnover Excel Extended"

    excel_file = fields.Binary('Download Report :- ')
    file_name = fields.Char('Excel File', size=64)

    products = fields.Many2one("product.product", "Product")
    product_category = fields.Many2one("product.category", "Category")
    # warehouse = fields.Many2one("stock.warehouse")
    # company = fields.Many2one("res.company", "Company")
    company_ids = fields.Many2many("res.company", 'rel_company_turnover', 'company_id', 'turnover_id', string="Company")
    warehouse_ids = fields.Many2many("stock.warehouse", 'rel_warehouse_turnover', 'warehouse_id', 'turnover_id', string="Warehouse")
    stock_opening = fields.Float("Opening Stock")
    stock_closing = fields.Float("Closing Stock")
    stock_average = fields.Float("Average Stock")
    sales = fields.Float("Sales")
    turnover = fields.Float("Turnover Ratio")
    wizard_id = fields.Many2one("inventory.turnover.report.wiz")
