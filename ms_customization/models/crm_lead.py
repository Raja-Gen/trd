# -*- coding: utf-8 -*-
from odoo import api, fields, models


class CrmLead(models.Model):
    _inherit = "crm.lead"

    def _ms_move_to_quotation_stage(self):
        for lead in self:
            if lead.stage_id.is_won or lead.stage_id.is_quotation_stage:
                continue
            # stage = self.env["crm.stage"].search(
            #     [
            #         ("is_quotation_stage", "=", True),
            #         ("team_ids", "in", lead.team_id.id),
            #     ],
            #     order="sequence",
            #     limit=1,
            # )
            stage = lead._stage_find(domain=[("is_quotation_stage", "=", True)])
            if not stage:
                continue
            lead.sudo().stage_id = stage.id

    def _ms_move_to_won_stage(self):
        """Mark each opportunity won, using Odoo's own team-aware won stage lookup."""
        for lead in self:
            if lead.stage_id.is_won:
                continue
            # stage = self.env["crm.stage"].search(
            #     [
            #         ("is_won", "=", True),
            #         ("team_ids", "in", lead.team_id.id),
            #     ],
            #     order="sequence",
            #     limit=1,
            # )
            stage = lead._stage_find(domain=[("is_won", "=", True)])
            if not stage:
                continue
            lead.sudo().stage_id = stage.id

    # --- Inventory items selected on the lead ---------------------------------
    warehouse_id = fields.Many2one(
        "stock.warehouse", string="Warehouse",
        domain="[('company_id', '=', company_id)]",
        help="Narrows the stock figures on the Inventory Items tab to one "
             "warehouse. Left empty, they cover the whole company.")
    lead_product_line_ids = fields.One2many(
        "crm.lead.product.line", "lead_id", string="Inventory Items",
        copy=True)
    lead_product_count = fields.Integer(
        string="Items", compute="_compute_lead_product_count")

    @api.depends("lead_product_line_ids")
    def _compute_lead_product_count(self):
        counts = {
            lead.id: count
            for lead, count in self.env["crm.lead.product.line"]._read_group(
                [("lead_id", "in", self.ids)], ["lead_id"], ["__count"])
        }
        for lead in self:
            lead.lead_product_count = counts.get(lead.id, 0)
