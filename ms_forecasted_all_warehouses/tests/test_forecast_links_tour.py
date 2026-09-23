# -*- coding: utf-8 -*-
from odoo.tests import HttpCase, tagged

RAJA_NAME = "RAJA INTERNATIONAL GENERAL TRADING (LLC)"


@tagged("post_install", "-at_install")
class TestForecastLinksTour(HttpCase):
    """The links are OWL: only a browser can prove they mount and open."""

    def test_incoming_outgoing_are_clickable(self):
        # This copy's enterprise subscription has lapsed; the expiry panel blocks
        # the UI and the tour with it.
        self.env["ir.config_parameter"].sudo().set_param(
            "database.expiration_date", "2099-12-31 00:00:00")

        # res.company.name is unique in this database, so the Raja company has to
        # be reused rather than created. The report opens on the FIRST warehouse
        # the client sees, so the moves go there - the figures are per product,
        # so other products' moves in that warehouse do not disturb the counts.
        company = self.env["res.company"].search([("name", "=", RAJA_NAME)], limit=1)
        self.assertTrue(company, "the Raja company is missing from this database")
        warehouse = self.env["stock.warehouse"].with_context(
            allowed_company_ids=[company.id]).search([("company_id", "=", company.id)], limit=1)
        self.assertTrue(warehouse, "the Raja company has no warehouse")

        user = self.env["res.users"].create({
            "name": "MS Links Tour User",
            "login": "ms_links_tour_user",
            "password": "ms_links_tour_user",
            "company_id": company.id,
            "company_ids": [(6, 0, [company.id])],
            "group_ids": [(6, 0, [
                self.env.ref("base.group_user").id,
                self.env.ref("stock.group_stock_manager").id,
            ])],
        })

        # Keep the kanban to one findable product.
        self.env["product.template"].search([("type", "!=", "service")]).write({"active": False})
        product = self.env["product.product"].create({
            "name": "MS Links Tour Product", "is_storable": True, "is_favorite": True})

        supplier = self.env.ref("stock.stock_location_suppliers")
        customer = self.env.ref("stock.stock_location_customers")

        def move(qty, incoming):
            m = self.env["stock.move"].with_company(company).create({
                "product_id": product.id,
                "product_uom_qty": qty,
                "company_id": company.id,
                "location_id": supplier.id if incoming else warehouse.lot_stock_id.id,
                "location_dest_id": warehouse.lot_stock_id.id if incoming else customer.id,
            })
            m._action_confirm()
            return m

        # 9 in across two moves (the tour counts the rows), 4 out.
        move(5.0, True)
        move(4.0, True)
        move(4.0, False)

        scoped = product.with_company(company).with_context(warehouse_id=warehouse.id)
        self.assertEqual(scoped.incoming_qty, 9.0)
        self.assertEqual(scoped.outgoing_qty, 4.0)

        self.start_tour("/odoo/action-stock.product_template_action_product",
                        "ms_forecast_links_tour", login=user.login, timeout=180)
