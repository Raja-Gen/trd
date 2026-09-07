# -*- coding: utf-8 -*-
from collections import defaultdict

from odoo import api, fields, models


class CrmLeadProductLine(models.Model):
    _name = "crm.lead.product.line"
    _description = "CRM Lead Inventory Item"
    _order = "lead_id, sequence, id"

    lead_id = fields.Many2one(
        "crm.lead", string="Lead", required=True, ondelete="cascade", index=True)
    sequence = fields.Integer(default=10)
    company_id = fields.Many2one(related="lead_id.company_id", store=True, index=True)

    product_id = fields.Many2one(
        "product.product", string="Product", required=True,
        domain="[('is_storable', '=', True)]",
        help="Only storable products are offered: consumables and services carry no stock.")
    name = fields.Char(string="Description", compute="_compute_name", store=True, readonly=False)
    product_uom_qty = fields.Float(
        string="Quantity", default=1.0, digits="Product Unit of Measure", required=True)
    product_uom_id = fields.Many2one(
        "uom.uom", string="UoM", compute="_compute_product_uom_id", store=True, readonly=False)

    # Stock figures, scoped to the lead's company and — when set — its warehouse.
    qty_available = fields.Float(
        string="On Hand", compute="_compute_stock", digits="Product Unit of Measure",
        help="Physically in stock now, in the product's own unit of measure.")
    virtual_available = fields.Float(
        string="Forecasted", compute="_compute_stock", digits="Product Unit of Measure",
        help="On hand, plus incoming, minus outgoing, in the product's own unit of measure.")
    free_qty = fields.Float(
        string="Free To Use", compute="_compute_stock", digits="Product Unit of Measure",
        help="On hand and not reserved for another operation, in the product's own unit of measure.")
    availability_status = fields.Selection(
        [("none", "No Product"), ("available", "In Stock"),
         ("partial", "Partial"), ("unavailable", "Out of Stock")],
        string="Availability", compute="_compute_stock",
        help="Compares Free To Use against the quantity required on this line.")

    @api.depends("product_id")
    def _compute_name(self):
        for line in self:
            line.name = line.product_id.get_product_multiline_description_sale() \
                if line.product_id else False

    @api.depends("product_id")
    def _compute_product_uom_id(self):
        for line in self:
            line.product_uom_id = line.product_id.uom_id

    @api.depends("product_id", "product_uom_qty", "product_uom_id",
                 "lead_id.company_id", "lead_id.warehouse_id")
    def _compute_stock(self):
        self.qty_available = self.virtual_available = self.free_qty = 0.0
        self.availability_status = "none"

        # Batch by (company, warehouse): the stock figures are read in a context
        # scoped to each, so lines sharing a scope can be read in one go.
        by_scope = defaultdict(lambda: self.env["crm.lead.product.line"])
        for line in self.filtered("product_id"):
            company = line.lead_id.company_id or self.env.company
            by_scope[(company.id, line.lead_id.warehouse_id.id)] |= line

        for (company_id, warehouse_id), lines in by_scope.items():
            ctx = {"allowed_company_ids": [company_id]}
            if warehouse_id:
                ctx["warehouse_id"] = warehouse_id
            # sudo: reading quantities walks stock.quant, which a salesperson
            # need not have access to. The scope is fixed by the context above,
            # so this cannot widen which company's stock is shown.
            products = lines.product_id.sudo().with_context(**ctx)
            qty_by_product = {p.id: p for p in products}
            for line in lines:
                product = qty_by_product[line.product_id.id]
                line.qty_available = product.qty_available
                line.virtual_available = product.virtual_available
                line.free_qty = product.free_qty
                line.availability_status = line._get_availability_status(product.free_qty)

    def _get_availability_status(self, free_qty):
        """Compare the required quantity with free stock, in the product's UoM."""
        self.ensure_one()
        required = self.product_uom_qty
        if self.product_uom_id and self.product_uom_id != self.product_id.uom_id:
            required = self.product_uom_id._compute_quantity(
                required, self.product_id.uom_id)
        if free_qty <= 0:
            return "unavailable"
        if free_qty >= required:
            return "available"
        return "partial"
