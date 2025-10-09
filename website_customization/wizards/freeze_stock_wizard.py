from odoo import models, fields, api, _
from odoo.exceptions import UserError
from datetime import timedelta

class FreezeStockWizard(models.TransientModel):
    _name = 'freeze.stock.wizard'
    _description = 'Freeze Stock Wizard'

    sale_id = fields.Many2one('sale.order', required=True)
    freeze_days = fields.Integer('Freeze Duration (Days)', default=1)

    @api.constrains('freeze_days')
    def _check_freeze_days(self):
        for rec in self:
            if rec.freeze_days <= 0 or rec.freeze_days > 30:
                raise UserError(_("You can freeze stock for 1 to 30 days only."))

    def action_confirm_freeze(self):
        order = self.sale_id

        for line in order.order_line:
            if line.product_id.type != 'product':
                continue

            freeze_records = self.env['stock.freeze.record'].sudo().search([
                ('product_id', '=', line.product_id.id)
            ])

            frozen_qty = sum(freeze_records.mapped('quantity'))
            remaining_qty = line.product_id.qty_available - frozen_qty

            if line.product_uom_qty > remaining_qty:
                user_info = ""
                for rec in freeze_records:
                    user_name = rec.create_uid.name if rec.create_uid else 'Unknown User'
                    user_info += "- %s: %.2f\n" % (user_name, rec.quantity)

                message = _(
                    "Cannot freeze product '%s'.\n\n"
                    "Total Stock: %.2f\n"
                    "Already Frozen: %.2f\n"
                    "Requested Quantity: %.2f\n"
                    "Maximum Available: %.2f\n\n"
                    "Frozen by Users:\n%s"
                ) % (
                    line.product_id.display_name,
                    line.product_id.qty_available,
                    frozen_qty,
                    line.product_uom_qty,
                    remaining_qty,
                    user_info or _("No freeze records found.")
                )
                raise UserError(message)

            self.env['stock.freeze.record'].sudo().create({
                'product_id': line.product_id.id,
                'order_id': order.id,
                'user_id': self.env.user.id, 
                'quantity': line.product_uom_qty,
            })

        expiry_date = fields.Datetime.now() + timedelta(days=self.freeze_days)
        order.write({
            'is_stock_frozen': True,
            'freeze_expiry_date': expiry_date,
        })

        return {'type': 'ir.actions.act_window_close'}
