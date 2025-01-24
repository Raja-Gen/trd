# -*- coding: utf-8 -*-

from odoo import fields,models,api

class HrPayslipWorkedDays(models.Model):
    _inherit = 'hr.payslip.worked_days'

    overtime_regular_hours = fields.Float(string="Regular Overtime Hours", compute="_compute_overtime_regular_hours")
    overtime_weekly_off_hours = fields.Float(string="Weekly Off Overtime Hours", compute="_compute_overtime_weekly_off_hours")
    overtime_public_holiday_hours = fields.Float(string="Public Holiday Overtime Hours", compute="_compute_overtime_public_holiday_hours")
    total_overtime_hours = fields.Float(string="Total Overtime Hours", compute="_compute_overtime_total_hours")

    @api.depends('payslip_id.employee_id', 'payslip_id.date_from', 'payslip_id.date_to')
    def _compute_overtime_regular_hours(self):
        for worked_day in self:
            overtime_hours = 0
            employee = worked_day.payslip_id.employee_id
            if not employee:
                worked_day.overtime_regular_hours = 0.0
                continue

            calendar = employee.resource_calendar_id
            if not calendar:
                worked_day.overtime_regular_hours = 0.0
                continue

            # Get working days from resource calendar
            working_days = {a.dayofweek for a in calendar.attendance_ids}
            # Get public holidays
            public_holidays = self.env['resource.calendar.leaves'].search([
            ('calendar_id', '=', calendar.id),
            ('date_from', '<=', worked_day.payslip_id.date_to),
            ('date_to', '>=', worked_day.payslip_id.date_from),
            ])
            holiday_dates = {fields.Date.to_date(leave.date_from) for leave in public_holidays}

            work_entry_ids = self.env['hr.work.entry'].search([
                ('employee_id', '=', employee.id),
                ('date_start', '>=', worked_day.payslip_id.date_from),
                ('date_stop', '<=', worked_day.payslip_id.date_to),
                ('work_entry_type_id.code', 'in', ['WORK100','OVERTIME']),
                ('state', '=', 'validated'),
            ])
            if work_entry_ids:
                for entry in work_entry_ids:
                    if str(entry.date_start.weekday()) in working_days:
                        overtime_hour = entry.duration - calendar.get_work_hours_count(entry.date_start, entry.date_stop)
                        if overtime_hour > 0:
                            overtime_hours += overtime_hour
            worked_day.overtime_regular_hours = overtime_hours

    @api.depends('payslip_id.employee_id', 'payslip_id.date_from', 'payslip_id.date_to')
    def _compute_overtime_weekly_off_hours(self):
        for worked_day in self:
            employee = worked_day.payslip_id.employee_id
            if not employee or not worked_day.payslip_id:
                worked_day.overtime_weekly_off_hours = 0.0
                continue

            calendar = employee.resource_calendar_id

            # Find the weekly day off
            working_days = {attendance.dayofweek for attendance in calendar.attendance_ids}
            all_days = {'0', '1', '2', '3', '4', '5', '6'}  # Monday to Sunday
            weekly_off_days = all_days - working_days

            if not weekly_off_days:
                worked_day.overtime_weekly_off_hours = 0.0
                continue

            overtime_hours = 0.0
            # Fetch validated work entries in the payslip period
            work_entries = self.env['hr.work.entry'].search([
            ('employee_id', '=', employee.id),
            ('date_start', '>=', worked_day.payslip_id.date_from),
            ('date_stop', '<=', worked_day.payslip_id.date_to),
            ('state', '=', 'validated')
            ])
            # Calculate overtime hours for work entries on weekly off days
            overtime_hours = sum(
            entry.duration for entry in work_entries
            if str(fields.Date.from_string(entry.date_start).weekday()) in weekly_off_days
            )
            worked_day.overtime_weekly_off_hours = overtime_hours

    @api.depends('payslip_id.employee_id', 'payslip_id.date_from', 'payslip_id.date_to')
    def _compute_overtime_public_holiday_hours(self):
        for worked_day in self:
         """
        Compute the total overtime hours worked during public holidays
        for each payslip, using resource.calendar.leaves to identify holidays.
        """
        for worked_day in self:
            overtime_hours = 0.0
            payslip = worked_day.payslip_id
            employee_calendar = payslip.employee_id.resource_calendar_id

            if not employee_calendar:
                worked_day.overtime_public_holiday_hours = 0.0
                continue

            # Check for work entries on the public holiday
            work_entries = self.env['hr.work.entry'].search([
                    ('work_entry_type_id.code', '=', 'LEAVE100'),
                    ('employee_id', '=', payslip.employee_id.id),
                    ('date_start', '>=', payslip.date_from),
                    ('date_stop', '<=', payslip.date_to),
                    ('state', '=', 'validated')
                ])
                # Sum up the duration (in hours) of the work entries
            overtime_hours = sum(work_entries.mapped('duration'))
            worked_day.overtime_public_holiday_hours = overtime_hours

    @api.depends('payslip_id.employee_id', 'payslip_id.date_from', 'payslip_id.date_to')
    def _compute_overtime_total_hours(self):
        for entry in self:
            overtime_regular_hours = entry.overtime_regular_hours * entry.hourly_rate * 1.25
            overtime_weekly_off_hours = entry.overtime_weekly_off_hours * entry.hourly_rate * 1.50
            overtime_public_holiday_hours = entry.overtime_public_holiday_hours * entry.hourly_rate * 2
            entry.total_overtime_hours = overtime_regular_hours + overtime_weekly_off_hours + overtime_public_holiday_hours
