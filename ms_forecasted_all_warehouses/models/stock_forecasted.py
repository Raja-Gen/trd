# -*- coding: utf-8 -*-
from collections import defaultdict

from odoo import fields, models
from odoo.tools import float_repr

# Context flag set by the client action when "All Warehouses" is picked.
ALL_WAREHOUSES = "ms_all_warehouses"


class StockForecasted_Product_Product(models.AbstractModel):
    _inherit = "stock.forecasted_product_product"

    # ------------------------------------------------------------------
    # Which warehouses "All Warehouses" covers
    # ------------------------------------------------------------------
    def _ms_aggregated_warehouses(self):
        """The warehouses the aggregated report covers.

        Scoped explicitly to the companies currently ticked in the company
        switcher, which is the same set the dropdown was built from. Record
        rules would normally narrow a bare search([]) the same way, but they are
        bypassed for the superuser - so a cron, a shell or a sudo() call would
        otherwise silently total up every company in the database. On a
        deployment with fifteen companies that is worth being explicit about.

        Deliberately NOT read from the client either: a browser must not be able
        to widen the scope of the figures it asks for.
        """
        return self.env["stock.warehouse"].search(
            [("company_id", "in", self.env.companies.ids)])

    # ------------------------------------------------------------------
    # Entry point
    # ------------------------------------------------------------------
    def _get_report_data(self, product_template_ids=False, product_ids=False):
        if not self.env.context.get(ALL_WAREHOUSES):
            return super()._get_report_data(product_template_ids, product_ids)

        warehouses = self._ms_aggregated_warehouses()
        single = self.with_context(**{ALL_WAREHOUSES: False})
        if len(warehouses) <= 1:
            # Nothing to aggregate - hand straight back to the standard report.
            return single._get_report_data(product_template_ids, product_ids)

        # One standard run per warehouse. Going back through the public method
        # (rather than super()) means every other module's contribution to the
        # report - sale_stock, purchase_stock, stock_account, product_expiry,
        # mrp - runs inside each pass exactly as it does normally.
        per_warehouse = [
            single.with_context(warehouse_id=warehouse.id)._get_report_data(
                product_template_ids=product_template_ids, product_ids=product_ids)
            for warehouse in warehouses
        ]

        res = self._ms_merge_report_data(per_warehouse)
        if any("value" in data for data in per_warehouse):
            # Recomputed rather than summed: the per-warehouse figures are
            # already formatted strings, and across companies they are not even
            # in the same currency.
            res["value"] = self._ms_total_value(
                warehouses, product_template_ids, product_ids)
        return res

    # ------------------------------------------------------------------
    # Merging
    # ------------------------------------------------------------------
    def _ms_merge_report_data(self, results):
        """Fold the per-warehouse reports into one."""
        res = dict(results[0])
        res["lines"] = []
        res["product"] = {}

        for data in results:
            res["lines"] += data.get("lines") or []
            for product_id, values in (data.get("product") or {}).items():
                if product_id in res["product"]:
                    values = self._ms_merge_dict(res["product"][product_id], values)
                res["product"][product_id] = values

        # The details table emits a product heading whenever the product changes
        # from one line to the next, so lines for one product have to stay
        # together. Concatenating per warehouse interleaves them; sort them back.
        order = {product_id: i for i, product_id in enumerate(res["product"])}
        res["lines"].sort(key=lambda line: order.get(line["product"]["id"], len(order)))

        # Top-level flags contributed by other modules (product_expiry's
        # use_expiration_date, for one) are true if true for any warehouse.
        for key, value in res.items():
            if isinstance(value, bool):
                res[key] = any(bool(data.get(key)) for data in results)
        return res

    def _ms_merge_dict(self, left, right):
        return {
            key: self._ms_merge_value(key, left.get(key), right.get(key))
            for key in list(left) + [k for k in right if k not in left]
        }

    def _ms_merge_value(self, key, left, right):
        """Combine one value from two warehouses.

        Everything the report puts under `product` is a quantity, so numbers are
        summed and that also picks up quantities added by modules this one has
        never heard of. The exceptions are named explicitly.
        """
        if left is None:
            return right
        if right is None:
            return left
        if key == "leadtime":
            # Soonest possible arrival across the warehouses.
            left_delay = (left or {}).get("total_delay", 0)
            right_delay = (right or {}).get("total_delay", 0)
            return left if left_delay <= right_delay else right
        if key == "uom":
            return left
        # bool before number: bool is a subclass of int.
        if isinstance(left, bool) or isinstance(right, bool):
            return bool(left) or bool(right)
        if isinstance(left, (int, float)) and isinstance(right, (int, float)):
            return left + right
        if isinstance(left, dict) and isinstance(right, dict):
            return self._ms_merge_dict(left, right)
        if isinstance(left, list) and isinstance(right, list):
            merged, seen = [], set()
            for item in left + right:
                marker = item.get("id") if isinstance(item, dict) else item
                if marker in seen:
                    continue
                seen.add(marker)
                merged.append(item)
            return merged
        return left

    # ------------------------------------------------------------------
    # Stock valuation across warehouses (stock_account's "Value On Hand")
    # ------------------------------------------------------------------
    def _ms_total_value(self, warehouses, product_template_ids, product_ids):
        Quant = self.env["stock.quant"]
        if "value" not in Quant._fields:
            return None
        if not self.env.user.has_group("stock.group_stock_manager"):
            return None

        location_ids = self.env["stock.location"].search(
            [("id", "child_of", warehouses.view_location_id.ids)]).ids
        if not location_ids:
            return None

        domain = [("location_id", "in", location_ids)]
        if product_template_ids:
            domain += [("product_id.product_tmpl_id", "in", product_template_ids)]
        else:
            domain += [("product_id", "in", product_ids)]

        # Odoo shows one figure in the user's company currency, so this shows
        # one figure in the user's company currency too. Amounts held by a
        # company on another currency are put through Odoo's own converter
        # first, rather than being added to it as if they were the same money.
        currency = self.env.company.currency_id
        totals = defaultdict(float)
        for quant in Quant.search(domain):
            totals[quant.company_id] += quant.value

        value = 0.0
        for company, amount in totals.items():
            from_currency = company.currency_id or currency
            if from_currency == currency:
                value += amount
            else:
                value += from_currency._convert(
                    amount, currency, company or self.env.company, fields.Date.context_today(self))
        return self._ms_format_value(currency, value)

    def _ms_format_value(self, currency, amount):
        text = float_repr(amount, precision_digits=currency.decimal_places)
        if currency.position == "after":
            return "%s %s" % (text, currency.symbol)
        return "%s %s" % (currency.symbol, text)
