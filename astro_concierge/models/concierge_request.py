# -*- coding: utf-8 -*-
# Module: astro_concierge
# Description: Custom Concierge Service Module for Astro Holding in Odoo 18.0

from odoo import models, fields, api, _
from odoo.exceptions import UserError

class ConciergeRequest(models.Model):
    _name = 'concierge.request'
    _description = 'Concierge Request'
    _inherit = ['mail.thread', 'mail.activity.mixin']
    _order = 'priority desc, request_date desc'

    name = fields.Char(string="Request Reference", required=True, copy=False, readonly=True,
                       default=lambda self: 'New')
    requester_id = fields.Many2one('res.users', string='Requested By', default=lambda self: self.env.user, tracking=True)
    assigned_to = fields.Many2one('res.users', string='Assigned To', tracking=True)
    category = fields.Selection([
        ('travel', 'Travel Booking'),
        ('logistics', 'Courier & Logistics'),
        ('vendor', 'Vendor Coordination'),
        ('vip', 'VIP Request'),
        ('client', 'Client Request'),
        ('reporting', 'Reporting'),
        ('follow_ups', 'Follow-ups'),
        ('other', 'Other')
    ], string='Request Type', required=True, tracking=True)
    description = fields.Text(string='Request Description', required=True)
    priority = fields.Selection([
        ('0', 'Low'),
        ('1', 'Normal'),
        ('2', 'High'),
        ('3', 'Urgent')
    ], string='Priority', default='1', tracking=True)
    request_date = fields.Datetime(string='Request Date', default=fields.Datetime.now, tracking=True)
    deadline = fields.Date(string='Deadline')
    state = fields.Selection([
        ('draft', 'New'),
        ('in_progress', 'In Progress'),
        ('done', 'Completed'),
        ('cancelled', 'Cancelled')
    ], string='Status', default='draft', tracking=True)
    feedback = fields.Text(string='Feedback / Remarks')
    is_confidential = fields.Boolean(string='Confidential Request', default=False)

    @api.model
    def create(self, vals):
        if not vals.get('name') or vals['name'] == 'New':
            vals['name'] = self.env['ir.sequence'].next_by_code('concierge.request') or '/'
        return super(ConciergeRequest, self).create(vals)

    def send_deadline_alerts(self):
        requests = self.search([
            ('deadline', '<=', fields.Date.today()),
            ('state', '!=', 'done'),
            ('state', '!=', 'cancelled')
        ])
        print("\n\n\t\trequests == ", requests)
        for request in requests:
            template = self.env.ref('astro_concierge.mail_template_deadline_alert')
            if template:
                template.send_mail(request.id, force_send=True)
