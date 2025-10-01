from odoo import models, api, fields
from odoo.exceptions import UserError
from datetime import timedelta

class SaleOrder(models.Model):
    _inherit = "sale.order"

    def action_confirm(self):
        for order in self:
            frozen_lines = order.order_line.filtered(
                lambda l: l.product_id.product_tmpl_id.freeze_stock
            )
            if frozen_lines:
                product_names = ", ".join(frozen_lines.mapped("product_id.display_name")[:5])
                if len(frozen_lines) > 5:
                    product_names += ", ..."
                raise UserError(
                    "Cannot confirm sale order because the following product(s) are frozen and cannot be sold: %s"
                    % product_names
                )
        return super(SaleOrder, self).action_confirm()

    @api.model
    def send_abandoned_cart_reminders(self):
        """Send reminder email to customers with website carts older than 24 hours"""
        cutoff_time = fields.Datetime.now() - timedelta(hours=24)
        carts = self.search([
            ('state', '=', 'draft'),
            ('website_id', '!=', False), 
            ('order_line', '!=', False),
            ('partner_id.email', '!=', False),  
        ])
        template = self.env.ref(
            'website_customization.email_template_abandoned_cart',
            raise_if_not_found=False
        )
        if template:
            for cart in carts:
                template.send_mail(cart.id, force_send=False)

    @api.model
    def clear_old_carts(self):
        """Clear only items in website carts older than 48 hours"""
        cutoff_time = fields.Datetime.now() - timedelta(hours=48)
        old_carts = self.search([
            ('state', '=', 'draft'),
            ('website_id', '!=', False),
            ('create_date', '<', cutoff_time),
        ])
        for cart in old_carts:
            cart.order_line.unlink()

