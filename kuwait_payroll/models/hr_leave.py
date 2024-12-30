#coding: utf-8
from odoo import models, fields, _
from odoo.exceptions import UserError


class HRLeave(models.Model):
    _inherit = "hr.leave"

    state = fields.Selection([
        ('draft', 'To Submit'),
        ('confirm', 'To Approve'),
        ('approve_1', 'HOD Approved'),
        ('approve_2', 'HR Approved'),
        ('approve_3', 'Management Approved'),
        ('refuse', 'Refused'),
        ('validate1', 'Second Approval'),
        ('validate', 'Approved')
    ])

    def action_approve_1(self):
        self.write({'state': 'approve_1'})

    def action_approve_2(self):
        self.write({'state': 'approve_2'})

    def action_approve_3(self):
        self.write({'state': 'approve_3'})
        self.write({'state': 'validate'})

    def action_confirm(self):
        for holiday in self:
            if holiday.employee_id.department_id:
                leave_approval = self.env['hr.employee.leave.approval'].sudo().search([
                    ('department_id', '=', holiday.employee_id.department_id.id),
                    ('company_id', '=', holiday.employee_company_id.id),
                ], limit=1)
                if leave_approval and leave_approval.manager_approval == 'not_required':
                    return self.sudo().write({'state': 'approve_1'})
        result = super().action_confirm()
        return result

    def action_refuse(self):
        if any(holiday.state in ['approve_1'] for holiday in self):
            return self.sudo().write({'state': 'refuse'})
        if any(holiday.state in ['approve_2'] for holiday in self):
            return self.sudo().write({'state': 'approve_1'})
        if any(holiday.state in ['approve_3'] for holiday in self):
            return self.sudo().write({'state': 'approve_2'})

        return super().action_refuse()

    def _check_approval_update(self, state):
        """ Check if target state is achievable. """
        if self.env.is_superuser():
            return



        current_employee = self.env.user.employee_id
        admin = self.env.user.has_group('base.group_system') #admin can do anything
        is_manager = self.env.user.has_group('hr_holidays.group_hr_holidays_manager')
        hr_job = self.env['hr.job'].sudo().search([
            ('name', '=ilike', 'HR & Admin Officer'),
            ('company_id', '=', self.env.company.id),
        ], limit=1)
        hr = self.env['hr.employee'].sudo().search([
            ('job_id', '=', hr_job.id),
            ('company_id', '=', self.env.company.id),
        ], limit=1) if hr_job else admin
        for holiday in self:
            val_type = holiday.validation_type
            is_hod = holiday.employee_id.parent_id == current_employee if holiday.employee_id.parent_id and not admin else admin
            is_hr = hr == current_employee if hr_job and not admin else admin
            if holiday.employee_id.department_id:
                leave_approval = self.env['hr.employee.leave.approval'].sudo().search([
                    ('department_id', '=', holiday.employee_id.department_id.id),
                    ('company_id', '=', holiday.employee_company_id.id),
                ], limit=1)
                if state == 'approve_1' and leave_approval and leave_approval.manager_approval == 'not_required':
                    is_hod = True
                elif state == 'approve_2' and leave_approval and current_employee != leave_approval.approver_ids.mapped('user_id')[0].employee_id:
                    is_hr = False
                elif state == 'approve_2' and leave_approval and current_employee == leave_approval.approver_ids.mapped('user_id')[0].employee_id:
                    is_hr = True
                elif state == 'approve_3' and leave_approval and current_employee != leave_approval.approver_ids.mapped('user_id')[1].employee_id:
                    admin = False
                elif state == 'approve_3' and leave_approval and current_employee == leave_approval.approver_ids.mapped('user_id')[1].employee_id:
                    admin = True

            if not is_manager and state != 'confirm':
                if state == 'draft':
                    if holiday.state == 'refuse':
                        raise UserError(_('Only a Time Off Manager can reset a refused leave.'))
                    if holiday.date_from and holiday.date_from.date() <= fields.Date.today():
                        raise UserError(_('Only a Time Off Manager can reset a started leave.'))
                    if holiday.employee_id != current_employee:
                        raise UserError(_('Only a Time Off Manager can reset other people leaves.'))
            if not is_hod and state not in ['confirm', 'draft', 'refuse', 'validate1', 'validate', 'approve_2', 'approve_3']:
                raise UserError(_('Only HOD can approve this.'))
            if not is_hr and state not in ['confirm', 'draft', 'refuse', 'validate1', 'validate', 'approve_1',
                                            'approve_3']:
                raise UserError(_('Only HR can approve this.'))
            if not admin and state not in ['confirm', 'draft', 'refuse', 'validate1', 'validate', 'approve_1',
                                        'approve_2']:
                raise UserError(_('Only Management can approve this.'))
                # else:
                #     if val_type == 'no_validation' and current_employee == holiday.employee_id:
                #         continue
                #     # use ir.rule based first access check: department, members, ... (see security.xml)
                #     holiday.check_access_rule('write')
                #
                #     # This handles states validate1 validate and refuse
                #     if holiday.employee_id == current_employee:
                #         raise UserError(_('Only a Time Off Manager can approve/refuse its own requests.'))
                #
                #     if (state == 'validate1' and val_type == 'both') and holiday.holiday_type == 'employee':
                #         if not is_officer and self.env.user != holiday.employee_id.leave_manager_id:
                #             raise UserError(
                #                 _('You must be either %s\'s manager or Time off Manager to approve this leave') % (
                #                     holiday.employee_id.name))
                #
                #     if (state == 'validate' and val_type == 'manager') and self.env.user != (
                #             holiday.employee_id | holiday.sudo().employee_ids).leave_manager_id:
                #         if holiday.employee_id:
                #             employees = holiday.employee_id
                #         else:
                #             employees = ', '.join(
                #                 holiday.employee_ids.filtered(lambda e: e.leave_manager_id != self.env.user).mapped(
                #                     'name'))
                #         raise UserError(_('You must be %s\'s Manager to approve this leave', employees))
                #
                #     if not is_officer and (
                #             state == 'validate' and val_type == 'hr') and holiday.holiday_type == 'employee':
                #         raise UserError(
                #             _('You must either be a Time off Officer or Time off Manager to approve this leave'))
