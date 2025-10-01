from odoo import http
from odoo.http import request

class CashPaymentController(http.Controller):

    @http.route('/payment/cash/create_tx', type='json', auth='public', website=True)
    def create_cash_tx(self, **kwargs):

        order = request.website.sale_get_order()
        if not order:
            return {'error': 'No active sale order'}

        order.state = 'sale'
        return {'success': True}

class CashPaymentController(http.Controller):

    @http.route(['/payment/cash/success'], type='http', auth='public', website=True)
    def payment_success(self, cash=None, **kwargs):
        return request.render("cash_payment_provider.payment_done", {})
