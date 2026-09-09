from odoo import models, fields, api

class SaleApprovalHistory(models.Model):
    _name = 'sale.approval.history'
    _description = 'Sale Approval History'
    # _order = 'date desc'

    sale_order_id = fields.Many2one('sale.order', string="Sale Order", ondelete='cascade')
    user_id = fields.Many2one('res.users', string="Approved By")
    action = fields.Selection([
        ('requested', 'Requested'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], string="Action")

    note = fields.Text(string="Notes")
    date = fields.Datetime(default=fields.Datetime.now)