# -*- coding: utf-8 -*-

from odoo import models, api,fields

class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'

    is_paid_maternity = fields.Boolean(
        string="Paid Maternity Leave",
        help="Check this box if this leave type is for Paid Maternity Leave."
    )
    is_unpaid_maternity = fields.Boolean(
        string="Unpaid Maternity Leave",
        help="Check this box if this leave type is for Unpaid Maternity Leave."
    )
