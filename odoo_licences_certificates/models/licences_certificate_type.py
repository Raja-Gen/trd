# -*- coding: utf-8 -*-
# Part of Probuse Consulting Service Pvt Ltd.
# See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _


class LicencescertificateType(models.Model):
    _name = "licences.certificate.type"
    _description = "Licences and Certificates Type"

    name = fields.Char(
        string='Name',
        required=True,
    )
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: