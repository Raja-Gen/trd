from odoo import models, api, fields, _
from odoo.exceptions import UserError
from datetime import timedelta

class SaleOrder(models.Model):
    _inherit = "sale.order"

    freeze_expiry_date = fields.Datetime("Freeze Expiry Date")
    is_stock_frozen = fields.Boolean("Stock Frozen", default=False)

    def action_confirm(self):
        for order in self:
            frozen_lines = order.order_line.filtered(
                lambda l: l.product_id.product_tmpl_id.freeze_stock
            )
            if frozen_lines:
                product_names = ", ".join(frozen_lines.mapped("product_id.display_name")[:5])
                if len(frozen_lines) > 5:
                    product_names += ", ..."
                raise UserError(_(
                    "Cannot confirm sale order because the following product(s) "
                    "are frozen and cannot be sold: %s"
                ) % product_names)
        return super(SaleOrder, self).action_confirm()

    @api.model
    def send_abandoned_cart_reminders(self):
        cutoff_time = fields.Datetime.now() - timedelta(hours=24)
        carts = self.search([
            ('state', '=', 'draft'),
            ('website_id', '!=', False),
            ('order_line', '!=', False),
            ('partner_id.email', '!=', False),
        ])
        template = self.env.ref('website_customization.email_template_abandoned_cart', raise_if_not_found=False)
        if template:
            for cart in carts:
                template.send_mail(cart.id, force_send=False)

    @api.model
    def clear_old_carts(self):
        cutoff_time = fields.Datetime.now() - timedelta(hours=48)
        old_carts = self.search([
            ('state', '=', 'draft'),
            ('website_id', '!=', False),
            ('create_date', '<', cutoff_time),
        ])
        for cart in old_carts:
            cart.order_line.unlink()

    def action_freeze_stock(self):
        """Open the wizard to freeze stock."""
        return {
            'name': _('Freeze Stock'),
            'type': 'ir.actions.act_window',
            'res_model': 'freeze.stock.wizard',
            'view_mode': 'form',
            'target': 'new',
            'context': {'default_sale_id': self.id},
        }

    def action_unfreeze_stock(self):
        """Unfreeze stock for this sale order."""
        StockFreeze = self.env['stock.freeze.record'].sudo()

        for order in self:
            order_records = StockFreeze.search([('order_id', '=', order.id)])
            affected_products = order_records.mapped('product_id')

            if order_records:
                order_records.unlink()

            for product in affected_products:
                total_remaining = sum(StockFreeze.search([
                    ('product_id', '=', product.id)
                ]).mapped('quantity')) or 0.0
                product.sudo().write({'freeze_qty': total_remaining})

            order.write({
                'is_stock_frozen': False,
                'freeze_expiry_date': False,
            })

    @api.model
    def _cron_unfreeze_expired_stock(self):
        """Automatically unfreeze expired stock freezes."""
        StockFreeze = self.env['stock.freeze.record'].sudo()
        expired_orders = self.search([
            ('is_stock_frozen', '=', True),
            ('freeze_expiry_date', '<', fields.Datetime.now())
        ])

        for order in expired_orders:
            order_records = StockFreeze.search([('order_id', '=', order.id)])
            affected_products = order_records.mapped('product_id')

            if order_records:
                order_records.unlink()

            for product in affected_products:
                total_remaining = sum(StockFreeze.search([
                    ('product_id', '=', product.id)
                ]).mapped('quantity')) or 0.0
                product.sudo().write({'freeze_qty': total_remaining})

            order.write({
                'is_stock_frozen': False,
                'freeze_expiry_date': False,
            })
