from odoo import models, fields, api

class SaleOrder(models.Model):
    _inherit = 'sale.order'

    def action_confirm(self):
        res = super(SaleOrder, self).action_confirm()
        for order in self:
            partner = order.partner_id
            if order.amount_total <= (partner.credit_limit - partner.credit_used):
                # Increase credit_used by order total
                partner.credit_used += order.amount_total
        return res
