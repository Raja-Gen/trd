import { patch } from "@web/core/utils/patch";
import { markup } from "@odoo/owl";
import { ForecastedHeader } from "@stock/stock_forecasted/forecasted_header";

// Incoming and Outgoing become clickable, the way On Hand already is. Offered
// only for the Raja group companies - the server decides that and hands the
// answer down in docs.ms_is_raja_company.
patch(ForecastedHeader.prototype, {
    /**
     * @param {"in"|"out"} direction
     */
    async _msOpenForecastMoves(direction) {
        const productIds = this.props.docs.product_variants_ids;
        if (!productIds || !productIds.length) {
            return;
        }
        const action = await this.orm.call(
            "product.product",
            "action_ms_open_forecast_moves",
            [productIds, direction],
            // The warehouses the report is showing. _get_domain_locations reads
            // warehouse_id off the context and accepts a list, so this scopes
            // the move list to exactly what the figure counted - one warehouse
            // normally, all of them under "All Warehouses".
            { context: { warehouse_id: this.props.docs.ms_warehouse_ids || [] } }
        );
        if (action.help) {
            // Without this the empty-list placeholder shows its raw HTML.
            action.help = markup(action.help);
        }
        return this.action.doAction(action);
    },
});
