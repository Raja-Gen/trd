from odoo import models, fields, api

class StockFreezeRecord(models.Model):
    _name = 'stock.freeze.record'
    _description = 'Stock Freeze Record'

    product_id = fields.Many2one('product.product', required=True)
    order_id = fields.Many2one('sale.order', required=True)
    user_id = fields.Many2one('res.users', string="Frozen By", required=True)
    quantity = fields.Float('Frozen Quantity', required=True)
