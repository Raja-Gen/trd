/** @odoo-module **/

import paymentForm from '@payment/js/payment_form';

paymentForm.include({
      
     /**
     * Simulate a feedback from a payment provider and redirect the customer to the status page.
     *
     * @override method from payment.payment_form
     * @private
     * @param {number} providerId - The id of the selected payment option's provider.
     * @param {string} providerCode - The code of the selected payment option's provider.
     * @param {number} paymentOptionId - The id of the selected payment option.
     * @param {string} paymentMethodCode - The code of the selected payment method, if any.
     * @param {string} flow - The payment flow, either 'token' or 'direct'.
     * @return {void}
     */
    async _prepareInlineForm(providerId, providerCode, paymentOptionId, paymentMethodCode, flow) {
        if (providerCode !== 'credit') {
            return this._super(...arguments);
        }
        this._setPaymentFlow('direct');
    },
    
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
            if (providerCode !== 'credit') {
                return this._super(...arguments);
            }

            try {
                // Call your controller to create the credit transaction
                await fetch("/payment/credit/create_tx", {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-Requested-With': 'XMLHttpRequest'
                    },
                    body: JSON.stringify({ flow: 'direct' }),
                });
                window.location.replace('/payment/credit/success');

            } catch (error) {
                console.error("Credit payment error:", error);
                alert("Unexpected error while processing credit payment.");
            }
        },

    });
