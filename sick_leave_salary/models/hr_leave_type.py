# -*- coding: utf-8 -*-

from odoo import models, api, fields


class HrLeaveType(models.Model):
    _inherit = "hr.leave.type"

    is_sick_leave = fields.Boolean(
        string="Sick Leave", help="Check this box if this leave type is for Sick Leave."
    )
