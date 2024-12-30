# -*- coding: utf-8 -*-

from odoo import models, fields


class HrExpenseSheet(models.Model):
    _inherit = 'hr.expense.sheet'

    date_end = fields.Date(string="End Date")
