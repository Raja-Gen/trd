#coding: utf-8
from odoo import models, fields, api, _
from odoo.exceptions import ValidationError


class HREmployeeLeaveApproval(models.Model):
    _name = "hr.employee.leave.approval"
    _description = 'Employee Leave Approval'
    _rec_name = 'department_id'

    department_id = fields.Many2one('hr.department', string='Department', required=True, check_company=True,
                              domain="[('company_id', '=', company_id)]")
    company_id = fields.Many2one(
        'res.company', 'Company', copy=False,
        required=True, index=True, default=lambda s: s.env.company)
    active = fields.Boolean(default=True)
    description = fields.Char(string="Description", translate=True)
    approval_minimum = fields.Integer(string="Minimum Approval", default="2", required=True)
    invalid_minimum = fields.Boolean(compute='_compute_invalid_minimum', store=True)
    invalid_minimum_warning = fields.Char(compute='_compute_invalid_minimum')
    manager_approval = fields.Selection([('not_required', 'Is No Required Approver'), ('required', 'Is Required Approver')],
                                        string="Employee's Manager", required=True, default='required',
                                        help="""How the employee's manager interacts with this type of approval.

            Is No Required Approver: the employee's manager approval will be skipped.
            Is Required Approver: the employee's manager will be required to approve the request.
        """)
    user_ids = fields.Many2many('res.users', compute='_compute_user_ids', string="Approver Users")
    approver_ids = fields.One2many('hr.employee.leave.approval.line', 'leave_approval_id', string="Approvers", required=True)
    approvers_ids = fields.Many2many('res.users', string="Approvers", compute='_compute_approvers_ids', store=True)

    @api.depends('approver_ids')
    def _compute_approvers_ids(self):
        for record in self:
            record['approvers_ids'] = record.approver_ids.mapped('user_id')

    @api.depends_context('lang')
    @api.depends('approval_minimum', 'approver_ids', 'manager_approval')
    def _compute_invalid_minimum(self):
        for record in self:
            # if record.approval_minimum > len(record.approver_ids) + int(bool(record.manager_approval)):
            if record.approval_minimum != len(record.approver_ids):
                record.invalid_minimum = True
            else:
                record.invalid_minimum = False
            record.invalid_minimum_warning = record.invalid_minimum and _(
                'Your minimum approval exceeds the total of default approvers.')

    @api.depends('approver_ids')
    def _compute_user_ids(self):
        for record in self:
            record.user_ids = record.approver_ids.user_id

    @api.constrains('approval_minimum', 'invalid_minimum')
    def _constrains_approver(self):
        if any(a.invalid_minimum for a in self):
            raise ValidationError(_('Approver can only be activated with 2 approver only.'))

    @api.constrains('department_id')
    def _constrains_department(self):
        for record in self:
            if record.department_id:
                dept_ids = self.env['hr.employee.leave.approval'].sudo().search([
                    ('id', '!=', record.id),
                    ('department_id', '=', record.department_id.id),
                    ('company_id', '=', record.company_id.id),
                ], limit=1)
                if dept_ids:
                    raise ValidationError(_('This department is already exist.'))



class HREmployeeLeaveApprovalLine(models.Model):
    _name = "hr.employee.leave.approval.line"
    _description = 'Employee Leave Approver'
    _rec_name = 'user_id'

    leave_approval_id = fields.Many2one('hr.employee.leave.approval', string='Emplyee Leave Approval', ondelete='cascade', required=True)
    company_id = fields.Many2one('res.company', related='leave_approval_id.company_id')
    user_id = fields.Many2one('res.users', string='User', ondelete='cascade', required=True,
                              check_company=True,
                              domain="[('company_ids', 'in', company_id), ('id', 'not in', existing_user_ids)]")

    existing_user_ids = fields.Many2many('res.users', compute='_compute_existing_user_ids')

    @api.depends('leave_approval_id')
    def _compute_existing_user_ids(self):
        for record in self:
            record.existing_user_ids = record.leave_approval_id.approver_ids.user_id
