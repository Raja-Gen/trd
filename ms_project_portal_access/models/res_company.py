# -*- coding: utf-8 -*-
from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    ms_project_portal = fields.Boolean(
        string="Portal access per task",
        help="Internal users can give portal users access to individual tasks of "
             "this company's projects, and a portal user only sees what was given "
             "to them personally, not what was given to others in their company.",
    )
