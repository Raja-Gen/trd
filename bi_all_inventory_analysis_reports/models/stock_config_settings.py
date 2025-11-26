# -*- coding: utf-8 -*-

from odoo import api, fields, models
from ast import literal_eval


class StockConfigurationSettings(models.TransientModel):
    _inherit = "res.config.settings"

    forcast_sales = fields.Boolean(string='Use Forcasted Sales For requisition')
    day_forcast = fields.Integer(string='Keep Stock in Days')
    past_sale = fields.Integer(string='Use Past Days')
    forcast_warehouse = fields.Boolean(string='Forcast Sales only For Warehouses')
    stock_expiry_days = fields.Integer(string="Generate Report For (Days)")
    include_expiry = fields.Boolean(string='Include Expiry Stock')
    report_type = fields.Selection([
        ('all', 'All'),
        ('location', 'Location'),
        ('warehouse', 'Warehouse')], string='Report Type', default='all')
    location_ids = fields.Many2many('stock.location', 'location_res_rel', 'loc_id', 'conf_loc_id', string='Location', store=True)
    warehouse_ids = fields.Many2many('stock.warehouse', 'ware_rel', 'ware_id', 'ware_loc_id', string='Warehouse', store=True)
    recipients_ids = fields.Many2many('res.partner', 'res_part_rel', 'part_id', 'conf_part_id', string='Mail Recipients', store=True)

    def get_values(self):
        res = super(StockConfigurationSettings, self).get_values()
        
        forcast_sales = self.env['ir.config_parameter'].sudo().get_param('bi_all_inventory_analysis_reports.forcast_sales') == 'True'
        forcast_warehouse = self.env['ir.config_parameter'].sudo().get_param('bi_all_inventory_analysis_reports.forcast_warehouse') == 'True'
        include_expiry = self.env['ir.config_parameter'].sudo().get_param('bi_all_inventory_analysis_reports.include_expiry') == 'True'
        
        day_forcast = int(self.env['ir.config_parameter'].sudo().get_param('bi_all_inventory_analysis_reports.day_forcast', 0) or 0)
        past_sale = int(self.env['ir.config_parameter'].sudo().get_param('bi_all_inventory_analysis_reports.past_sale', 0) or 0)
        
        stock_expiry_days = int(self.env['ir.config_parameter'].sudo().get_param('bi_all_inventory_analysis_reports.stock_expiry_days', 0) or 0)
        
        report_type = self.env['ir.config_parameter'].sudo().get_param('bi_all_inventory_analysis_reports.report_type')
        location_ids = self.env['ir.config_parameter'].sudo().get_param('bi_all_inventory_analysis_reports.location_ids')
        warehouse_ids = self.env['ir.config_parameter'].sudo().get_param('bi_all_inventory_analysis_reports.warehouse_ids')
        recipients_ids = self.env['ir.config_parameter'].sudo().get_param('bi_all_inventory_analysis_reports.recipients_ids')

        if location_ids:
            location_ids_list = [(6, 0, literal_eval(location_ids))]
        else:
            location_ids_list = False

        if warehouse_ids:
            warehouse_ids_list = [(6, 0, literal_eval(warehouse_ids))]
        else:
            warehouse_ids_list = False

        if recipients_ids:
            recipients_ids_list = [(6, 0, literal_eval(recipients_ids))]
        else:
            recipients_ids_list = False

        res.update(
            forcast_sales=forcast_sales,
            day_forcast=day_forcast,
            forcast_warehouse=forcast_warehouse,
            past_sale=past_sale,
            stock_expiry_days=stock_expiry_days,
            include_expiry=include_expiry,
            report_type=report_type,
            location_ids=location_ids_list,
            warehouse_ids=warehouse_ids_list,
            recipients_ids=recipients_ids_list
        )

        return res


    def set_values(self):
        res = super(StockConfigurationSettings, self).set_values()
        self.env['ir.config_parameter'].sudo().set_param('bi_all_inventory_analysis_reports.forcast_sales', self.forcast_sales)
        self.env['ir.config_parameter'].sudo().set_param('bi_all_inventory_analysis_reports.day_forcast', self.day_forcast)
        self.env['ir.config_parameter'].sudo().set_param('bi_all_inventory_analysis_reports.forcast_warehouse', self.forcast_warehouse)
        self.env['ir.config_parameter'].sudo().set_param('bi_all_inventory_analysis_reports.past_sale', self.past_sale)

        self.env['ir.config_parameter'].sudo().set_param('bi_all_inventory_analysis_reports.stock_expiry_days', str(self.stock_expiry_days))
        self.env['ir.config_parameter'].sudo().set_param('bi_all_inventory_analysis_reports.include_expiry', self.include_expiry)
        self.env['ir.config_parameter'].sudo().set_param('bi_all_inventory_analysis_reports.report_type', self.report_type)
        self.env['ir.config_parameter'].sudo().set_param('bi_all_inventory_analysis_reports.location_ids', self.location_ids.ids)
        self.env['ir.config_parameter'].sudo().set_param('bi_all_inventory_analysis_reports.warehouse_ids', self.warehouse_ids.ids)
        self.env['ir.config_parameter'].sudo().set_param('bi_all_inventory_analysis_reports.recipients_ids', self.recipients_ids.ids)

        return res
