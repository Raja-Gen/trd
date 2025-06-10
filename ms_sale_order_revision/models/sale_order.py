# -*- coding: utf-8 -*-
from odoo import models, fields, api, _
import re


class SaleOrder(models.Model):
    _inherit = 'sale.order'

    order_revise = fields.Char(string='Revision', default="", copy=False)

    def _compute_display_name(self):
        for order in self:
            if order.order_revise:
                order.display_name = f"{order.name}-{order.order_revise}"
            else:
                order.display_name = order.name

    @api.model_create_multi
    def create(self, vals_list):
        orders = super().create(vals_list)
        for order in orders:
            order._compute_display_name()
        return orders

    def write(self, vals):
        if 'order_line' in vals:
            for order in self:
                old_lines = order.order_line.mapped('product_id')
                super(SaleOrder, order).write(vals)
                new_lines = order.order_line.mapped('product_id')

                added = set(new_lines) - set(old_lines)
                removed = set(old_lines) - set(new_lines)

                removed_products = []
                added_products = []
                message_passed = False
                message_body = ""
                if added:
                    index = 1
                    for prod in added:
                        added_products.append(_(f"{index}. {prod.name}"))
                        index += 1
                    # Post message
                    message_body = f"Added {len(added_products)} products: {', '.join(added_products)}"

                    order.message_post(body=message_body)
                    message_passed = True

                if removed:
                    index = 1
                    for prod in removed:
                        removed_products.append(_(f"{index}. {prod.name}"))
                        index += 1
                    # Post message
                    message_body = f"Removed {len(removed)} products: {', '.join(removed_products)}"
                    order.message_post(body=message_body)
                    message_passed = True

                if message_passed:
                    # Update revision
                    print(f"\n\t\torder_revise - {order.order_revise}, ")
                    if order.order_revise:
                        current = int(order.order_revise[1:])
                        order.order_revise = f"R{current + 1}"
                    else:
                        order.order_revise = "R1"


                    # Update display name
                    order._compute_display_name()
                return True

        return super().write(vals)


class SaleOrderLine(models.Model):
    _inherit = 'sale.order.line'

    def write(self, vals):
        if vals.get('product_id'):
            message_parts = []
            old_product = self.product_id.name
            super(SaleOrderLine, self).write(vals)
            new_product = self.product_id.name
            # Post message
            self.order_id.message_post(body=f"Exchanged Products: {old_product} -> {new_product}".join(message_parts))
            if self.order_id.order_revise:
                current = int(self.order_id.order_revise[1:])
                self.order_id.order_revise = f"R{current + 1}"
            else:
                self.order_id.order_revise = "R1"
            self.order_id._compute_display_name()
            return True
        return super(SaleOrderLine, self).write(vals)
