from odoo import models, fields

class PurchaseApprovalHistory(models.Model):
    _name = 'purchase.approval.history'
    _description = 'Purchase Approval History'
    # _order = 'date desc'

    purchase_order_id = fields.Many2one(
        'purchase.order', string="Purchase Order", ondelete='cascade'
    )
    user_id = fields.Many2one('res.users', string="User")
    action = fields.Selection([
        ('requested', 'Requested'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    ], default='requested')

    note = fields.Text()
    date = fields.Datetime(default=fields.Datetime.now)