/** @odoo-module **/

import { patch } from '@web/core/utils/patch';
import { PaymentForm } from '@payment/interactions/payment_form';

patch(PaymentForm.prototype, {
    // #=== DOM MANIPULATION ===#

    /**
     * Prepare the inline form of Cash for direct payment.
     *
     * @override method from @payment/js/payment_form
     * @private
     * @param {number} providerId - The id of the selected payment option's provider.
     * @param {string} providerCode - The code of the selected payment option's provider.
     * @param {number} paymentOptionId - The id of the selected payment option
     * @param {string} paymentMethodCode - The code of the selected payment method, if any.
     * @param {string} flow - The online payment flow of the selected payment option.
     * @return {void}
     */
    async _prepareInlineForm(providerId, providerCode, paymentOptionId, paymentMethodCode, flow) {
        if (providerCode !== 'cash') {
            this._super(...arguments);
            return;
        } else if (flow === 'token') {
            return;
        }
        this._setPaymentFlow('direct');
    },

    // #=== PAYMENT FLOW ===#

    /**
     * Simulate a feedback from a payment provider and redirect the customer to the status page.
     *
     * @override method from payment.payment_form
     * @private
     * @param {string} providerCode - The code of the selected payment option's provider.
     * @param {number} paymentOptionId - The id of the selected payment option.
     * @param {string} paymentMethodCode - The code of the selected payment method, if any.
     * @param {object} processingValues - The processing values of the transaction.
     * @return {void}
     */
    async _processDirectFlow(providerCode, paymentOptionId, paymentMethodCode, processingValues) {
    if (providerCode !== 'cash') {
        this._super(...arguments);
        return;
    }

    try {
        // Call your cash payment RPC
        const result = await fetch("/payment/cash/create_tx", {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-Requested-With': 'XMLHttpRequest' },
            body: JSON.stringify({
                provider_id: processingValues.provider_id,
                payment_option_id: processingValues.payment_option_id,
                flow: 'direct',
            }),
        }).then(r => r.json());

        if (result) {
            // Directly redirect to success page
            window.location.replace('/payment/cash/success');
        } else if (result.error) {
            alert(result.error);
        } else {
            alert("Cash Payment Failed. Please try again.");
        }
    } catch (error) {
        console.error("Cash payment error:", error);
        alert("Unexpected error while processing cash payment.");
    }
},

});