# -*- coding: utf-8 -*-
from odoo import models, fields, api, _


class ProductBrand(models.Model):
    _name = "product.brand"
    _description = "Product Brand"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _order = "sequence, name"

    name = fields.Char(
        string="Brand Name", required=True, translate=True, tracking=True
    )
    sequence = fields.Integer(
        string="Sequence",
        default=10,
        help="Gives the sequence order when displaying a list of brands.",
    )
    logo = fields.Image(string="Logo", max_width=256, max_height=256)
    description = fields.Text(string="Description", translate=True)
    active = fields.Boolean(
        string="Active",
        default=True,
        help="If unchecked, it will allow you to hide the brand"
             " without removing it.",
        tracking=True,
    )
    company_id = fields.Many2one(
        "res.company",
        string="Company", tracking=True,
        default=lambda self: self.env.company,
        domain=lambda self:[('id', 'in', self.env.companies.ids)],
        help="Specify a company if this brand is company-specific."
             " Leave empty for global brands.",
    )
    product_ids = fields.One2many(
        "product.template", "brand_id", string="Products", readonly=True
    )
    products_count = fields.Integer(
        string="Number of Products",
        compute="_compute_products_count",
    )

    _name_company_uniq = models.Constraint(
        "unique(name, company_id)",
        "Brand name must be unique per company!",
    )

    @api.depends("product_ids")
    def _compute_products_count(self):
        """Computes the number of products associated with this brand."""
        for brand in self:
            brand.products_count = len(brand.product_ids)

    def action_view_products(self):
        """Action to view products associated with this brand."""
        self.ensure_one()
        action_ref = self.env["ir.actions.act_window"]._for_xml_id(
            "product.product_template_action_all"
        )
        if not action_ref:
            action_ref = self.env["ir.actions.act_window"]._for_xml_id(
                "product.product_template_action"
            )

        # Create a copy of the action dictionary to avoid modifying the original
        action = dict(action_ref or {})
        if not action:
            # This should ideally not happen if 'product' module is installed
            return {"type": "ir.actions.act_window_close"}

        action["domain"] = [("brand_id", "=", self.id)]
        ctx = dict(self.env.context)
        ctx.pop("search_default_filter_to_sell", None)
        ctx.pop("search_default_filter_consumable", None)
        ctx.pop("search_default_filter_services", None)
        ctx["default_brand_id"] = self.id
        action["context"] = ctx
        # Set a specific name for the action window
        action["display_name"] = _("Products of %s") % self.name
        return action
