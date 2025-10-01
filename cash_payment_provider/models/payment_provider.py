from odoo import models, fields
import logging

_logger = logging.getLogger(__name__)


class PaymentProviderCash(models.Model):
    _inherit = "payment.provider"

    code = fields.Selection(
        selection_add=[("cash", "Cash on Delivery")],
        ondelete={"cash": "set default"},
    )
    name = fields.Char(default="Cash on Delivery")


