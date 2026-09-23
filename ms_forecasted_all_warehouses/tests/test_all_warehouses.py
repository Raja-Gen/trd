# -*- coding: utf-8 -*-
from odoo.tests.common import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestForecastedAllWarehouses(TransactionCase):
    """Aggregation of the Forecasted Report across warehouses."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Report = cls.env["stock.forecasted_product_product"]
        cls.Quant = cls.env["stock.quant"]

        cls.company_a = cls.env["res.company"].create({"name": "MS Test Company A"})
        cls.company_b = cls.env["res.company"].create({"name": "MS Test Company B"})
        # allowed_company_ids only narrows to companies the user actually belongs
        # to; without this the environment silently falls back to every company
        # the user has, and the aggregation would look far too wide.
        cls.env.user.company_ids = [(4, cls.company_a.id), (4, cls.company_b.id)]

        # Two warehouses in company A, one in company B.
        cls.wh_a1 = cls.env["stock.warehouse"].create({
            "name": "MS Test WH A1", "code": "MSA1", "company_id": cls.company_a.id})
        cls.wh_a2 = cls.env["stock.warehouse"].create({
            "name": "MS Test WH A2", "code": "MSA2", "company_id": cls.company_a.id})
        cls.wh_b1 = cls.env["stock.warehouse"].create({
            "name": "MS Test WH B1", "code": "MSB1", "company_id": cls.company_b.id})

        cls.product = cls.env["product.product"].create({
            "name": "MS Test Forecast Product", "is_storable": True})

        cls.qty_a1, cls.qty_a2, cls.qty_b1 = 10.0, 25.0, 7.0
        for warehouse, qty in ((cls.wh_a1, cls.qty_a1),
                               (cls.wh_a2, cls.qty_a2),
                               (cls.wh_b1, cls.qty_b1)):
            cls.Quant.with_company(warehouse.company_id)._update_available_quantity(
                cls.product, warehouse.lot_stock_id, qty)

    def _on_hand(self, report):
        """The On Hand figure the report header would show."""
        data = report._get_report_data(product_ids=self.product.ids)
        return sum(values["quantity_on_hand"] for values in data["product"].values())

    def _report(self, companies, warehouse=None, all_warehouses=False):
        context = {"allowed_company_ids": companies.ids}
        if warehouse:
            context["warehouse_id"] = warehouse.id
        if all_warehouses:
            context["ms_all_warehouses"] = True
        return self.Report.with_company(companies[0]).with_context(**context)

    # --- the standard report must be untouched --------------------------------

    def test_single_warehouse_unchanged(self):
        """Without the flag the report still covers exactly one warehouse."""
        self.assertEqual(self._on_hand(self._report(self.company_a, self.wh_a1)), self.qty_a1)
        self.assertEqual(self._on_hand(self._report(self.company_a, self.wh_a2)), self.qty_a2)

    def test_flag_absent_means_no_aggregation(self):
        """An unset flag must not aggregate, even with several warehouses about."""
        report = self._report(self.company_a, self.wh_a1)
        self.assertNotEqual(self._on_hand(report), self.qty_a1 + self.qty_a2)

    # --- aggregation ----------------------------------------------------------

    def test_all_warehouses_sums_within_a_company(self):
        report = self._report(self.company_a, self.wh_a1, all_warehouses=True)
        self.assertEqual(self._on_hand(report), self.qty_a1 + self.qty_a2)

    def test_all_warehouses_is_independent_of_the_selected_one(self):
        """The warehouse still in context must not skew the aggregate."""
        from_a1 = self._on_hand(self._report(self.company_a, self.wh_a1, all_warehouses=True))
        from_a2 = self._on_hand(self._report(self.company_a, self.wh_a2, all_warehouses=True))
        self.assertEqual(from_a1, from_a2)

    def test_lines_are_grouped_per_product(self):
        """Concatenating per warehouse must not interleave products."""
        data = self._report(self.company_a, self.wh_a1, all_warehouses=True)._get_report_data(
            product_ids=self.product.ids)
        seen, order = set(), []
        for line in data["lines"]:
            product_id = line["product"]["id"]
            if product_id not in seen:
                seen.add(product_id)
                order.append(product_id)
            else:
                self.assertEqual(product_id, order[-1],
                                 "lines for one product must stay contiguous")

    # --- multi-company --------------------------------------------------------

    def test_other_companies_are_excluded(self):
        """Only the companies active in the switcher are aggregated."""
        report = self._report(self.company_a, self.wh_a1, all_warehouses=True)
        self.assertEqual(self._on_hand(report), self.qty_a1 + self.qty_a2,
                         "company B's stock must not leak into company A's report")

    def test_both_companies_active(self):
        both = self.company_a | self.company_b
        report = self._report(both, self.wh_a1, all_warehouses=True)
        self.assertEqual(self._on_hand(report),
                         self.qty_a1 + self.qty_a2 + self.qty_b1)

    def test_scope_follows_record_rules_not_the_client(self):
        """The server picks the warehouses itself; the browser cannot widen them."""
        report = self._report(self.company_a, self.wh_a1, all_warehouses=True)
        warehouses = report._ms_aggregated_warehouses()
        self.assertIn(self.wh_a1, warehouses)
        self.assertIn(self.wh_a2, warehouses)
        self.assertNotIn(self.wh_b1, warehouses)

    # --- merging --------------------------------------------------------------

    def test_merge_sums_numbers_and_ors_flags(self):
        merged = self.Report._ms_merge_value("anything", 2.5, 4.0)
        self.assertEqual(merged, 6.5)
        self.assertIs(self.Report._ms_merge_value("flag", False, True), True)
        self.assertEqual(
            self.Report._ms_merge_value("qty", {"in": 1.0, "out": 2.0}, {"in": 3.0, "out": 0.5}),
            {"in": 4.0, "out": 2.5})

    def test_merge_keeps_the_soonest_leadtime(self):
        soon, later = {"total_delay": 2, "details": {}}, {"total_delay": 9, "details": {}}
        self.assertEqual(self.Report._ms_merge_value("leadtime", later, soon), soon)
        self.assertEqual(self.Report._ms_merge_value("leadtime", soon, later), soon)

    def test_merge_deduplicates_documents(self):
        left = [{"id": 1, "name": "SO1"}, {"id": 2, "name": "SO2"}]
        right = [{"id": 2, "name": "SO2"}, {"id": 3, "name": "SO3"}]
        self.assertEqual(
            [d["id"] for d in self.Report._ms_merge_value("draft_sale_orders", left, right)],
            [1, 2, 3])

    def test_value_on_hand_is_one_figure_in_the_company_currency(self):
        """Displayed exactly as Odoo displays it: one figure, one currency."""
        report = self._report(self.company_a | self.company_b, self.wh_a1,
                              all_warehouses=True)
        value = report._ms_total_value(
            report._ms_aggregated_warehouses(), False, self.product.ids)
        if value is None:
            self.skipTest("stock_account is not installed")
        self.assertNotIn(" + ", value, "the figure must not be split per currency")
        self.assertIn(self.env.company.currency_id.symbol, value)

    def test_merge_keeps_the_unit_of_measure(self):
        self.assertEqual(self.Report._ms_merge_value("uom", "Units", "Units"), "Units")
