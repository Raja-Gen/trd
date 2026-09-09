import { patch } from "@web/core/utils/patch";
import { _t } from "@web/core/l10n/translation";
import { ForecastedWarehouseFilter } from "@stock/stock_forecasted/forecasted_warehouse_filter";
import { StockForecasted } from "@stock/stock_forecasted/stock_forecasted";

// Context flag read by ms_forecasted_all_warehouses on the server.
export const MS_ALL_WAREHOUSES = "ms_all_warehouses";
// Sentinel used only inside the dropdown; never reaches the server.
export const MS_ALL_ID = "ms_all";

patch(ForecastedWarehouseFilter.prototype, {
    get activeWarehouse() {
        if (this.context[MS_ALL_WAREHOUSES]) {
            return { id: MS_ALL_ID, name: _t("All Warehouses") };
        }
        return super.activeWarehouse;
    },

    get warehousesItems() {
        // The whole filter is hidden by core when there is only one warehouse,
        // so this entry can never be the only one on offer.
        return [
            {
                id: MS_ALL_ID,
                label: _t("All Warehouses"),
                onSelected: () => this.props.setWarehouseInContext(MS_ALL_ID),
            },
            ...super.warehousesItems,
        ];
    },
});

patch(StockForecasted.prototype, {
    async updateWarehouse(id) {
        if (id === MS_ALL_ID) {
            const wasAll = Boolean(this.context[MS_ALL_WAREHOUSES]);
            this.context[MS_ALL_WAREHOUSES] = true;
            // warehouse_id is left set on purpose. Core reads it to decide
            // whether to fall back to the first warehouse and to decide whether
            // to render the graph at all, and the Replenish button uses it as
            // its default. The server ignores it while the flag is on.
            if (!this.context.warehouse_id && this.warehouses.length) {
                this.context.warehouse_id = this.warehouses[0].id;
            }
            if (!wasAll) {
                await this.reloadReport();
            }
            return;
        }
        // Picking a single warehouse again drops back to standard behaviour.
        this.context[MS_ALL_WAREHOUSES] = false;
        return super.updateWarehouse(id);
    },

    get graphDomain() {
        if (!this.context[MS_ALL_WAREHOUSES]) {
            return super.graphDomain;
        }
        const domain = [
            ["state", "=", "forecast"],
            ["warehouse_id", "in", this.warehouses.map((warehouse) => warehouse.id)],
        ];
        if (this.resModel === "product.template") {
            domain.push(["product_tmpl_id", "=", this.productId]);
        } else if (this.resModel === "product.product") {
            domain.push(["product_id", "=", this.productId]);
        }
        return domain;
    },
});
