# -*- coding: utf-8 -*-
from odoo import api, models


class SaleOrder(models.Model):
    _inherit = "sale.order"

    def _ms_leads_to_sync(self):
        return self.opportunity_id.filtered(lambda lead: lead.type == "opportunity")

    @api.model_create_multi
    def create(self, vals_list):
        orders = super().create(vals_list)
        quotations = orders.filtered(lambda order: order.state in ("draft", "sent"))
        # Covers quotations built in code, where no onchange runs. A quotation
        # that already has lines is left exactly as it was passed in.
        for order in quotations:
            if order.opportunity_id and not order.order_line:
                order.order_line = order._ms_prepare_lines_from_lead()
        quotations._ms_leads_to_sync()._ms_move_to_quotation_stage()
        return orders

    def write(self, vals):
        res = super().write(vals)
        # Covers linking an existing quotation to an opportunity after the fact.
        if vals.get("opportunity_id"):
            quotations = self.filtered(lambda order: order.state in ("draft", "sent"))
            quotations._ms_leads_to_sync()._ms_move_to_quotation_stage()
        return res

    def action_confirm(self):
        res = super().action_confirm()
        self._ms_leads_to_sync()._ms_move_to_won_stage()
        return res

    # --- Pre-fill quotation lines from the lead's inventory items -------------
    def _ms_prepare_lines_from_lead(self):
        """Order line values mirroring the opportunity's Inventory Items."""
        self.ensure_one()
        return [
            (0, 0, {
                "product_id": line.product_id.id,
                "product_uom_qty": line.product_uom_qty,
                "product_uom_id": line.product_uom_id.id,
            })
            for line in self.opportunity_id.lead_product_line_ids
        ]

    @api.onchange("opportunity_id")
    def _ms_onchange_opportunity_fill_lines(self):
        """Fill the quotation from the lead as soon as it is picked in the form.

        Only ever fills an empty quotation, so lines already keyed in by hand are
        never overwritten.
        """
        if self.opportunity_id and not self.order_line:
            self.order_line = self._ms_prepare_lines_from_lead()
