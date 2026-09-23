# -*- coding: utf-8 -*-

from odoo import models, fields


class AsKPICategory(models.Model):
    _name = 'as.kpi.category'
    _description = 'KPI Category'
    _order = 'name'

    # Fields
    name = fields.Char(string='Category Name', required=True)
