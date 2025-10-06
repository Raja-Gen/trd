from odoo import http
from odoo.http import request
from odoo.exceptions import UserError

class CreditPaymentController(http.Controller):

    @http.route('/payment/credit/create_tx', type='json', auth='public', website=True)
    def create_credit_tx(self, **kwargs):
        order = request.website.sale_get_order()
        if not order:
            return {'error': 'No active sale order'}

        partner = order.partner_id
        amount = order.amount_total
        available_credit = partner.credit_limit - partner.credit_used

        if amount > available_credit:
            return {
                'error': f"You don’t have sufficient credit. "
                         f"Available: {available_credit}, Required: {amount}"
            }

        provider = request.env['payment.provider'].sudo().search([('code', '=', 'credit')], limit=1)
        if not provider:
            return {'error': 'Credit Payment Provider not configured'}

        payment_method = request.env['payment.method'].sudo().search([
            ('provider_ids', '=', provider.id)
        ], limit=1)

        if not payment_method:
            return {'error': 'No payment method configured for Credit provider'}

        existing_tx = request.env['payment.transaction'].sudo().search([
            ('sale_order_ids', 'in', [order.id]),
            ('state', 'in', ['draft','pending'])
        ], limit=1)

        if existing_tx:
            tx = existing_tx
        else:
            tx_values = {
                'amount': amount,
                'currency_id': order.currency_id.id,
                'provider_id': provider.id,
                'payment_method_id': payment_method.id,
                'partner_id': partner.id,
                'sale_order_ids': [(6, 0, [order.id])],
            }
            tx = request.env['payment.transaction'].sudo().create(tx_values)

        tx._post_process_after_done()
        tx.sudo().write({'state': 'draft', 'provider_reference': 'Credit Payment'})
        order.action_confirm()

        return {'success': True}

    @http.route(['/payment/credit/success'], type='http', auth='public', website=True)
    def payment_success(self, credit=None, **kwargs):
        return request.render("credit_payment_provider.payment_done", {})

    @http.route(['/shop/payment/options'], type='json', auth='public', website=True)
    def get_payment_options(self, **kwargs):
        order = request.website.sale_get_order()
        options = []

        if not order:
            return {'options': options}

        partner = order.partner_id
        available_credit = partner.credit_limit - partner.credit_used

        if order.amount_total <= available_credit:
            provider = request.env['payment.provider'].sudo().search([('code', '=', 'credit')], limit=1)
            if provider:
                payment_method = request.env['payment.method'].sudo().search([('provider_ids', '=', provider.id)], limit=1)
                if payment_method:
                    options.append({
                        'provider_code': 'credit',
                        'provider_id': provider.id,
                        'payment_method_id': payment_method.id,
                        'label': 'Pay with Credit'
                    })

        return {'options': options, 'available_credit': available_credit}
