# -*- coding: utf-8 -*-
import json

from odoo.tests.common import TransactionCase, tagged

RAJA_NAME = "RAJA INTERNATIONAL GENERAL TRADING (LLC)"


@tagged("post_install", "-at_install")
class TestForecastMoveLinks(TransactionCase):
    """Clickable Incoming / Outgoing on the Forecasted Report."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        Company = cls.env["res.company"]
        cls.raja = Company.search([("name", "=", RAJA_NAME)], limit=1) \
            or Company.create({"name": RAJA_NAME})
        cls.other = Company.create({"name": "MS Links Not Raja"})
        cls.env.user.company_ids = [(4, cls.raja.id), (4, cls.other.id)]

        cls.warehouse = cls.env["stock.warehouse"].search(
            [("company_id", "=", cls.raja.id)], limit=1) or cls.env["stock.warehouse"].create(
            {"name": "MS Links WH", "code": "MSLW", "company_id": cls.raja.id})
        cls.product = cls.env["product.product"].create(
            {"name": "MS Links Product", "is_storable": True})
        cls.supplier_loc = cls.env.ref("stock.stock_location_suppliers")
        cls.customer_loc = cls.env.ref("stock.stock_location_customers")

    def _move(self, qty, incoming=True):
        move = self.env["stock.move"].with_company(self.raja).create({
            "product_id": self.product.id,
            "product_uom_qty": qty,
            "company_id": self.raja.id,
            "location_id": self.supplier_loc.id if incoming else self.warehouse.lot_stock_id.id,
            "location_dest_id": self.warehouse.lot_stock_id.id if incoming else self.customer_loc.id,
        })
        move._action_confirm()
        return move

    def _report(self, company, **ctx):
        return self.env["stock.forecasted_product_product"].with_company(company).with_context(
            allowed_company_ids=[company.id], warehouse_id=self.warehouse.id, **ctx)

    # --- the flag that shows the links ---------------------------------------

    def test_links_offered_for_a_raja_company(self):
        data = self._report(self.raja)._get_report_data(product_ids=self.product.ids)
        self.assertTrue(data["ms_is_raja_company"])

    def test_links_not_offered_for_another_company(self):
        data = self.env["stock.forecasted_product_product"].with_company(self.other).with_context(
            allowed_company_ids=[self.other.id])._get_report_data(product_ids=self.product.ids)
        self.assertFalse(data["ms_is_raja_company"],
                         "the links must not be offered outside the Raja companies")

    # --- the scope handed to the client ---------------------------------------

    def test_warehouse_scope_single(self):
        data = self._report(self.raja)._get_report_data(product_ids=self.product.ids)
        self.assertEqual(data["ms_warehouse_ids"], self.warehouse.ids)

    def test_warehouse_scope_all_warehouses(self):
        data = self._report(self.raja, ms_all_warehouses=True)._get_report_data(
            product_ids=self.product.ids)
        expected = self.env["stock.warehouse"].search(
            [("company_id", "in", [self.raja.id])]).ids
        self.assertEqual(sorted(data["ms_warehouse_ids"]), sorted(expected),
                         "under All Warehouses the links must cover every warehouse")

    # --- the list behind the number ------------------------------------------

    def test_incoming_moves_add_up_to_the_figure(self):
        """The whole point: the list must equal the number that was clicked."""
        self._move(7.0, incoming=True)
        self._move(3.0, incoming=True)
        product = self.product.with_company(self.raja).with_context(
            warehouse_id=self.warehouse.id)
        domain = product._ms_forecast_move_domain("in")
        listed = sum(self.env["stock.move"].search(domain).mapped("product_qty"))
        self.assertEqual(listed, product.incoming_qty)
        self.assertEqual(listed, 10.0)

    def test_outgoing_moves_add_up_to_the_figure(self):
        self._move(4.0, incoming=False)
        product = self.product.with_company(self.raja).with_context(
            warehouse_id=self.warehouse.id)
        domain = product._ms_forecast_move_domain("out")
        listed = sum(self.env["stock.move"].search(domain).mapped("product_qty"))
        self.assertEqual(listed, product.outgoing_qty)
        self.assertEqual(listed, 4.0)

    def test_incoming_and_outgoing_do_not_overlap(self):
        self._move(7.0, incoming=True)
        self._move(4.0, incoming=False)
        product = self.product.with_company(self.raja).with_context(
            warehouse_id=self.warehouse.id)
        moves_in = self.env["stock.move"].search(product._ms_forecast_move_domain("in"))
        moves_out = self.env["stock.move"].search(product._ms_forecast_move_domain("out"))
        self.assertFalse(moves_in & moves_out, "a move cannot be both incoming and outgoing")

    # --- the action itself ----------------------------------------------------

    def test_action_opens_the_moves(self):
        self._move(7.0, incoming=True)
        product = self.product.with_company(self.raja).with_context(
            warehouse_id=self.warehouse.id)
        action = product.action_ms_open_forecast_moves("in")
        self.assertEqual(action["res_model"], "stock.move")
        self.assertEqual(action["name"], "Incoming")
        self.assertEqual(action["display_name"], "Incoming",
                         "the breadcrumb reads display_name, not name")
        self.assertNotIn("search_default_done", action["context"],
                         "the stock action defaults to DONE moves, the opposite of Incoming")
        self.assertEqual(
            sum(self.env["stock.move"].search(action["domain"]).mapped("product_qty")), 7.0)

    def test_action_accepts_the_warehouse_list_the_client_sends(self):
        """The client passes docs.ms_warehouse_ids, which is a list."""
        self._move(7.0, incoming=True)
        product = self.product.with_company(self.raja).with_context(
            warehouse_id=[self.warehouse.id])
        action = product.action_ms_open_forecast_moves("in")
        found = self.env["stock.move"].search(action["domain"])
        self.assertEqual(sum(found.mapped("product_qty")), 7.0,
                         "a warehouse list must scope the same as a bare id")

    def test_end_to_end_as_a_restricted_user_from_a_template_report(self):
        """Mirrors the browser path: template report, non-superuser, list context."""
        self._move(5.0, incoming=True)
        self._move(4.0, incoming=True)
        user = self.env["res.users"].create({
            "name": "MS Links E2E User", "login": "ms_links_e2e_user",
            "company_id": self.raja.id, "company_ids": [(6, 0, [self.raja.id])],
            "group_ids": [(6, 0, [self.env.ref("base.group_user").id,
                                  self.env.ref("stock.group_stock_manager").id])],
        })
        template = self.product.product_tmpl_id

        # 1. what the report hands the client
        report = self.env["stock.forecasted_product_template"].with_user(user).with_context(
            allowed_company_ids=[self.raja.id], warehouse_id=self.warehouse.id)
        docs = report._get_report_data(product_template_ids=template.ids)
        self.assertTrue(docs["ms_is_raja_company"])
        self.assertEqual(docs["ms_warehouse_ids"], self.warehouse.ids)
        self.assertEqual(docs["product_variants_ids"], self.product.ids)

        # 2. the figure the user sees
        shown = sum(v["incoming_qty"] for v in docs["product"].values())
        self.assertEqual(shown, 9.0)

        # 3. the click, with exactly the arguments the client sends
        action = self.env["product.product"].with_user(user).browse(
            docs["product_variants_ids"]).with_context(
            allowed_company_ids=[self.raja.id],
            warehouse_id=docs["ms_warehouse_ids"],
        ).action_ms_open_forecast_moves("in")
        moves = self.env["stock.move"].with_user(user).search(action["domain"])
        self.assertEqual(len(moves), 2, "both incoming moves must be listed")
        self.assertEqual(sum(moves.mapped("product_qty")), shown,
                         "the list must add up to the figure that was clicked")

    def test_action_domain_can_be_sent_to_the_browser(self):
        """The regression that cost a cycle: _get_domain_locations() returns lazy
        SQL subqueries, which serialise to "<Query: SELECT ...>" and give the
        client an empty list. The action must carry plain ids."""
        self._move(7.0, incoming=True)
        product = self.product.with_company(self.raja).with_context(
            warehouse_id=[self.warehouse.id])
        action = product.action_ms_open_forecast_moves("in")
        json.dumps(action["domain"])          # must not raise
        self.assertEqual([term[0] for term in action["domain"]], ["id"])
        self.assertEqual(
            sum(self.env["stock.move"].browse(action["domain"][0][2]).mapped("product_qty")),
            7.0)
