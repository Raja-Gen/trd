# -*- coding: utf-8 -*-

from odoo import fields,models,api

class HPPayslipLine(models.Model):
    _inherit = 'hr.payslip.line'

    @api.onchange('amount', 'quantity', 'rate')
    def _onchange_recalculate_total(self):
        """
        Recalculates the total whenever amount, quantity, or rate changes.
        """
        for record in self:
            record.total = record.amount * record.quantity * record.rate / 100.0

    
