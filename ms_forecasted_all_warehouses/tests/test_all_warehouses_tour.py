# -*- coding: utf-8 -*-
from odoo.tests import HttpCase, tagged


@tagged("post_install", "-at_install")
class TestForecastedAllWarehousesTour(HttpCase):
    """The dropdown entry is OWL code: only a browser can prove it mounts."""

    def test_all_warehouses_option(self):
        # This is a copy of a production database whose enterprise subscription
        # has lapsed; the expiry panel blocks the UI and the tour with it. Push
        # it out of the way - the copy is thrown away after the run.
        self.env["ir.config_parameter"].sudo().set_param(
            "database.expiration_date", "2099-12-31 00:00:00")

        company = self.env.user.company_id
        # Keep the kanban to a single, findable product.
        self.env["product.template"].search([("type", "!=", "service")]).write({"active": False})

        wh_one = self.env["stock.warehouse"].search(
            [("company_id", "=", company.id)], limit=1)
        if not wh_one:
            wh_one = self.env["stock.warehouse"].create(
                {"name": "MS Tour WH One", "code": "MST1", "company_id": company.id})
        wh_two = self.env["stock.warehouse"].create(
            {"name": "MS Tour WH Two", "code": "MST2", "company_id": company.id})

        # This database's uid 2 does not use the stock "admin"/"admin" login, so
        # the tour drives a user created here with a password we know.
        tour_user = self.env["res.users"].create({
            "name": "MS Tour User",
            "login": "ms_tour_user",
            "password": "ms_tour_user",
            "company_id": company.id,
            "company_ids": [(6, 0, [company.id])],
            "group_ids": [(6, 0, [
                self.env.ref("base.group_user").id,
                self.env.ref("stock.group_stock_manager").id,
            ])],
        })

        product = self.env["product.product"].create({
            "name": "MS Tour Forecast Product",
            "is_storable": True,
            "is_favorite": True,
        })
        # 4 in the first warehouse, 7 in the second: 11 when aggregated, and the
        # three figures are distinct so the assertions cannot pass by accident.
        self.env["stock.quant"]._update_available_quantity(product, wh_one.lot_stock_id, 4)
        self.env["stock.quant"]._update_available_quantity(product, wh_two.lot_stock_id, 7)

        self.start_tour("/odoo/action-stock.product_template_action_product",
                        "ms_forecasted_all_warehouses_tour",
                        login=tour_user.login, timeout=180)
