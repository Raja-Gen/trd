import { patch } from '@web/core/utils/patch';
import { WebsiteSale } from '@website_sale/interactions/website_sale';

patch(WebsiteSale.prototype, {
    /**
     * Refresh the custom "Available: X" message with the quantity of the
     * variant that is currently selected, instead of the template total.
     * The message is hidden when that variant has nothing left: the
     * "Out of Stock" badge from website_sale_stock already says so.
     *
     * @override
     */
    _onChangeCombination(ev, parent, combination) {
        super._onChangeCombination(...arguments);

        const container = parent.querySelector('.o_wc_variant_availability');
        if (!container) {
            return;
        }

        const qty = parseFloat(combination.website_variant_qty_available) || 0;
        const qtyEl = container.querySelector('.o_wc_variant_available_qty');
        if (qtyEl) {
            qtyEl.textContent =
                combination.website_variant_qty_available_str ?? String(Math.floor(qty));
        }
        container.classList.toggle('d-none', qty <= 0);
    },
});
