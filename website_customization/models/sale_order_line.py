from odoo import models, fields, api, _
from odoo.exceptions import UserError

class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    @api.constrains('product_id', 'product_uom_qty')
    def _check_quantity_with_frozen(self):
        """Prevent saving quotation if requested qty exceeds available stock after freeze."""
        for line in self:
            if line.product_id.type != 'product':
                continue

            freeze_records = self.env['stock.freeze.record'].sudo().search([
                ('product_id', '=', line.product_id.id)
            ])
            frozen_qty = sum(freeze_records.mapped('quantity'))
            available_qty = line.product_id.qty_available - frozen_qty

            if line.product_uom_qty > available_qty:
                user_info = ""
                for rec in freeze_records:
                    user_name = rec.create_uid.name if rec.create_uid else 'Unknown User'
                    user_info += "- %s: %.2f\n" % (user_name, rec.quantity)

                message = _(
                    "Cannot create quotation for product '%s'.\n\n"
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
                    available_qty,
                    user_info or _("No freeze records found.")
                )
                raise UserError(message)
