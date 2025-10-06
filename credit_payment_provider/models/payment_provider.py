from odoo import models, fields, _
from odoo.exceptions import UserError
import logging
_logger = logging.getLogger(__name__)

class PaymentProviderCash(models.Model):
    _inherit = "payment.provider"

    code = fields.Selection(
        selection_add=[("credit", "Credit Payment")],
        ondelete={"credit": "set default"},
    )
    name = fields.Char(default="Credit Payment")


class PaymentTransaction(models.Model):
    _inherit = 'payment.transaction'

    def _check_credit_limit(self):
        for tx in self:
            partner = tx.partner_id
            available_credit = partner.credit_limit - partner.credit_used
            if tx.amount > available_credit:
                raise UserError(_(
                    "You don’t have sufficient credit to buy this product. "
                    "Available credit: %s, Required: %s"
                ) % (available_credit, tx.amount))

    def _create_credit_transaction(self, values):
        self._check_credit_limit()
        tx = self.create(values)
        tx._post_process_after_done()
        return tx

    def _post_process_after_done(self):
        for tx in self:
            if tx.provider_code == 'credit':
                # Increment stored credit_used_from_tx
                partner = tx.partner_id.sudo()
                partner.write({
                    'credit_used_from_tx': partner.credit_used_from_tx + tx.amount
                })
            # Mark transaction draft to avoid re-processing
            tx.sudo().write({
                'state': 'draft',
                'provider_reference': 'Credit Payment',
            })
            _logger.info("Credit transaction processed: %s for partner %s", tx.id, tx.partner_id.id)