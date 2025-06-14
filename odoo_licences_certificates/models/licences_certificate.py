# -*- coding: utf-8 -*-
# Part of Probuse Consulting Service Pvt Ltd.
# See LICENSE file for full copyright and licensing details.

from odoo import models, fields, api, _
from datetime import datetime, timedelta, date
from odoo.exceptions import UserError, ValidationError


class Licencescertificate(models.Model):
    _name = "record.certificate"
    _description = "Certificates History"
    _inherit = ['mail.thread']

    name = fields.Char(
        string='Certificate Name',
        required=True,
    )
    active = fields.Boolean(
        string='Active',
        default=True,
    )
    number = fields.Char(
        string='Certificate Number',
        required=True,
    )
    certificate_type = fields.Selection(
        selection=[('employee', 'Employee'),
                   ('customer/supplier/contact', 'Customer/Supplier/Contact'),
                   ('user','User')],
        string='Belongs To',
        copy=False,
        required=True,
        default='customer/supplier/contact'
    )
    employee_id = fields.Many2one(
        'hr.employee',
        string="Employee",
        #required=False,
    )
    partner_id = fields.Many2one(
        'res.partner',
        'Customer/Supplier/Contact'
    )
    start_date = fields.Date(
        string="Start Date",
        required=True
    )
    end_date = fields.Date(
        string="Expire Date",
        required=True
    )
    notes = fields.Text(
        string='Internal Notes',
        copy=True,
    )
    note = fields.Text(
        string='Description',
    )
    type_id = fields.Many2one(
        'licences.certificate.type',
        string="Certificate Types",
    )
    company_id = fields.Many2one(
        'res.company',
        string='Company',
        required=True,
        default=lambda self: self.env.user.company_id
    )
    user_id = fields.Many2one(
        'res.users',
        string="Responsible User",
        required=True,
        default=lambda self: self.env.user.id,
        copy=False,
    )
    reminder_day = fields.Integer(
        string="Expired Reminder Day"
    )
    state = fields.Selection(
        [('a_draft', 'New'),
         ('b_active', 'Active'),
         ('c_expire_soon', 'Expire Soon'),
         ('d_expired', 'Expired'),
         ('cancel', 'Cancelled')],
        string='Status',
        default='a_draft',
        copy=False,
        track_visibility="onchange"
    )
    project_id = fields.Many2one(
        'project.project',
        string="Project",
        required=False
    )
    task_id = fields.Many2one(
        'project.task',
        string='Task',
        required=False
    )
    product_id = fields.Many2one(
        'product.product',
        required=False,
        string="Product"
    )
    achievement = fields.Html(
        string="Achievement",
    )
    issuses_by = fields.Many2one(
        'res.partner',
        string="Issued by",
        required=True
    )
    custom_user_id = fields.Many2one(
        'res.users',
        string="User"
    )

    # @api.multi
    def action_reset_draft(self):
        return self.write({'state': 'a_draft'})

    # @api.multi
    def action_active(self):
        return self.write({'state': 'b_active'})

    # @api.multi
    def action_expire_soon(self):
        return self.write({'state': 'c_expire_soon'})

    # @api.multi
    def action_expired(self):
        return self.write({'state': 'd_expired'})

    # @api.multi
    def action_cancle(self):
        return self.write({'state': 'cancel'})

    # @api.multi
    def unlink(self):
        for rec in self:
            if rec.state not in ('a_draft', 'cancel'):
                raise UserError(_('You cannot delete certificate.'))
        return super(Licencescertificate, self).unlink()

    @api.model
    def _run_licences_certificate_cron_add(self):
        licences_certificate = self.env['record.certificate'].search([])
        for rec in licences_certificate:
            expire_date = rec.end_date - timedelta(days=rec.reminder_day)
            if expire_date == fields.date.today():
                rec.write({'state': 'c_expire_soon'})
                # mail_template_id = self.env.ref('odoo_licences_certificates.odoo_certificate_record_email_templte')
                mail_template_id = self.env.ref('odoo_licences_certificates.odoo_certificate_record_email_templte_view')
                ctx = self._context.copy()
                ctx.update({'name': str(rec.name)  +  rec.end_date.strftime('%m/%d/%y')})
                mail_template_id.with_context(ctx).send_mail(rec.id)
            if rec.end_date == fields.date.today():
                rec.write({'state': 'd_expired'})
                # mail_template_id = self.env.ref('odoo_licences_certificates.odoo_certificate_record_expire_email_templte')
                mail_template_id = self.env.ref('odoo_licences_certificates.odoo_certificate_record_expire_email_templte_view')
                ctx = self._context.copy()
                ctx.update({'name': str(rec.name)  +  rec.end_date.strftime('%m/%d/%y')})
                mail_template_id.with_context(ctx).send_mail(rec.id)
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4: