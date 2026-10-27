# -*- coding: utf-8 -*-
from odoo import _
from odoo.exceptions import UserError, ValidationError
from odoo.http import request, route

from odoo.addons.website_sale.controllers.main import WebsiteSale


class WebsiteSaleCustomerPricelist(WebsiteSale):

    def _apply_selectable_pricelist(self, pricelist_id):
        """Let a customer switch to one of their own website pricelists.

        Core only accepts `selectable` pricelists or the partner's default one,
        but customer pricelists are usually hidden from everybody else.
        """
        website = request.env['website'].get_current_website()
        customer_pricelists = website._get_customer_website_pricelists()
        if pricelist_id in customer_pricelists.ids and website.is_pricelist_available(pricelist_id):
            self._apply_pricelist(pricelist=customer_pricelists.browse(pricelist_id))
            return True
        return super()._apply_selectable_pricelist(pricelist_id)

    @route('/shop/payment/on_account', type='http', methods=['POST'], auth='public', website=True, sitemap=False)
    def shop_payment_on_account(self, **post):
        """Confirm the cart against the customer's credit limit, without payment."""
        order_sudo = request.cart
        if redirection := self._check_cart_and_addresses(order_sudo):
            return redirection
        if self._get_shop_payment_errors(order_sudo):
            return request.redirect('/shop/payment')
        info = order_sudo._get_pay_on_account_info()
        if not info or not info['enough']:
            return request.redirect('/shop/payment')
        try:
            with request.env.cr.savepoint():
                order_sudo._check_cart_is_ready_to_be_paid()
                order_sudo.placed_on_account = True
                order_sudo._validate_order()
        except (UserError, ValidationError) as e:
            request.env.invalidate_all()
            order_sudo.shop_warning = str(e)
            return request.redirect('/shop/cart')
        request.session['sale_last_order_id'] = order_sudo.id
        order_sudo.message_post(body=_("Order placed on account from the website."))
        request.website.sale_reset()
        return request.redirect('/shop/confirmation')
