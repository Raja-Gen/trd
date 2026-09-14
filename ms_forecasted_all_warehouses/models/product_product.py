# -*- coding: utf-8 -*-
from odoo import _, models


class ProductProduct(models.Model):
    _inherit = "product.product"

    def _ms_forecast_move_domain(self, direction):
        """The moves that make up the Incoming / Outgoing figure.

        Built from the same pieces Odoo uses to compute those numbers in
        `_compute_quantities_dict`: the location domain from
        `_get_domain_locations()` - which reads `warehouse_id` straight off the
        context, so passing the report's warehouses scopes it identically - plus
        the same "not yet done" states. Reusing them is what guarantees the list
        adds up to the number the user clicked.
        """
        _quant_loc, move_in_loc, move_out_loc = self._get_domain_locations()
        return [
            ("product_id", "in", self.ids),
            ("state", "in", ("waiting", "confirmed", "assigned", "partially_available")),
        ] + (move_in_loc if direction == "in" else move_out_loc)

    def action_ms_open_forecast_moves(self, direction):
        """Open the moves behind the Incoming / Outgoing figure."""
        moves = self.env["stock.move"].search(self._ms_forecast_move_domain(direction))
        action = self.env["ir.actions.actions"]._for_xml_id("stock.stock_move_action")
        # Resolved to plain ids on purpose. _get_domain_locations() builds its
        # location clauses as lazy SQL subqueries: they work server-side, but they
        # cannot be serialised into an action, so the client would receive
        # "<Query: SELECT ...>" as a literal string and show an empty list.
        # Searching here also guarantees the rows are exactly the ones counted.
        action["domain"] = [("id", "in", moves.ids)]
        label = _("Incoming") if direction == "in" else _("Outgoing")
        # display_name too: the breadcrumb prefers it, and without it the user
        # lands on a list still titled "Moves Analysis".
        action["name"] = action["display_name"] = label
        # The action ships with search_default_done, which would filter to moves
        # already done - the exact opposite of what these figures count.
        action["context"] = {"search_default_future": 0}
        action["views"] = [
            (self.env.ref("stock.view_move_tree").id, "list"),
            (False, "form"),
        ]
        return action
