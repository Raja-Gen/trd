# -*- coding: utf-8 -*-
from odoo import api, fields, models


class StockMove(models.Model):
    _inherit = "stock.move"

    landed_cost_value = fields.Monetary(
        string="Landed Cost",
        compute="_compute_landed_cost",
        currency_field="company_currency_id",
        help="Landed costs posted against this move, from validated landed cost records.",
    )
    landed_cost_unit = fields.Monetary(
        string="Landed Cost / Unit",
        compute="_compute_landed_cost",
        currency_field="company_currency_id",
        help="Landed cost booked against this move, divided by the move quantity.",
    )

    @api.depends("quantity")
    def _compute_landed_cost(self):
        # sudo: stock.valuation.adjustment.lines is restricted to Inventory
        # Administrators, but the amount is shown to anyone allowed to see the
        # move's cost columns.
        grouped = self.env["stock.valuation.adjustment.lines"].sudo()._read_group(
            [("move_id", "in", self.ids), ("cost_id.state", "=", "done")],
            ["move_id"],
            ["additional_landed_cost:sum"],
        )
        totals = {move.id: total for move, total in grouped}
        for move in self:
            value = totals.get(move._origin.id, 0.0)
            move.landed_cost_value = value
            move.landed_cost_unit = value / move.quantity if move.quantity else 0.0
