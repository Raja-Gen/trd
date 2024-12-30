# -*- coding: utf-8 -*-

from datetime import date
from odoo import api, fields, models
from odoo.osv import expression


class Employee(models.Model):
    _inherit = "hr.employee"

    
    anual_leave_salary = fields.Monetary(string="Annual leave until today",related="contract_id.anual_leave_salary")
    eos_indiminity = fields.Monetary(string="EOS indiminity until today",related="contract_id.eos_indiminity")
    anual_leave_days = fields.Float(string="Annual leave Days",related="contract_id.anual_leave_days")
    eos_indiminity_days = fields.Float(string="EOS Days",related="contract_id.eos_indiminity_days")
    leave_taken = fields.Float(string="taken leaves",related="contract_id.leave_taken")


