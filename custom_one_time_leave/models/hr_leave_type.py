# -*- coding: utf-8 -*-

from odoo import models, api,fields

class HrLeaveType(models.Model):
    _inherit = 'hr.leave.type'

    is_one_time_leave = fields.Boolean(
        string='One-Time Leave',
        help='Indicates whether this leave type is for One-Time Leave allocation.'
    )
