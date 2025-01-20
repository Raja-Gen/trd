# -*- coding: utf-8 -*-

import pytz
from odoo import fields,models,api
from datetime import datetime, timedelta

class HrPayslipWorkedDays(models.Model):
    _inherit = 'hr.payslip.worked_days'

    hourly_rate = fields.Float(string="Hours Rate", compute="_compute_attendance_deductions", store=True)
    total_delay_hours = fields.Float(string="Total Delay Hours", compute="_compute_attendance_deductions", store=True)
    total_checkin_delay = fields.Float(string="Total Check-In Delay", compute="_compute_attendance_deductions", store=True)
    total_checkout_delay = fields.Float(string="Total Check-Out Delay", compute="_compute_attendance_deductions", store=True)
    attendance_deduction = fields.Float(string="Attendance Deduction", compute="_compute_attendance_deductions", store=True)

    @api.depends('payslip_id.date_from', 'payslip_id.date_to', 'payslip_id.employee_id')
    def _compute_attendance_deductions(self):
        for entry in self:
            payslip = entry.payslip_id
            if not payslip:
                continue  # Skip if no payslip is linked

            date_from = payslip.date_from
            date_to = payslip.date_to

            start_dt = datetime.combine(date_from, datetime.min.time())
            end_dt = datetime.combine(date_to, datetime.min.time())

            # Get the resource calendar (working schedule) from the contract
            contract = entry.contract_id
            resource_calendar = contract.resource_calendar_id

            # Fetch the allowed late minutes from the settings
            config_settings = self.env['res.config.settings'].search([], limit=1)
            allow_late_coming_minutes = config_settings.allow_late_coming_minutes if config_settings else 0
            total_working_hours = config_settings.total_working_hours if config_settings else 8
            total_working_days_per_month = config_settings.total_working_days_per_month if config_settings else 26

            # Compute total required working hours for the payslip period
            if resource_calendar:
                total_required_hours = resource_calendar.get_work_hours_count(start_dt, end_dt, compute_leaves=True)
            else:
                total_required_hours = 8 * 26  # Fallback to 9 hours/day for 22 working days

            total_required_hours = max(total_required_hours, 1)  # Ensure total_required_hours is valid

            # Get the employee's timezone
            employee_timezone = payslip.employee_id.tz or 'UTC'
            user_tz = pytz.timezone(employee_timezone)

            # Fetch actual worked hours from hr.attendance for the employee
            attendance_records = self.env['hr.attendance'].search([
                ('employee_id', '=', payslip.employee_id.id),
                ('check_in', '>=', start_dt),
                ('check_out', '<=', end_dt)
            ])

            actual_worked_hours = 0
            total_checkin_delay = 0.0
            total_checkout_delay = 0.0

            for attendance in attendance_records:
                if attendance.check_in and attendance.check_out:
                    actual_worked_hours += (attendance.check_out - attendance.check_in).total_seconds() / 3600.0

                    if resource_calendar:
                        # Get the day of the week for the attendance record
                        dayofweek = str(attendance.check_in.weekday())
                        
                        # Get the working hours for the day
                        working_hours = resource_calendar.attendance_ids.filtered(lambda r: r.dayofweek == dayofweek)
                        
                        if working_hours:
                            # Calculate expected start time
                            expected_start_time = attendance.check_in.replace(
                                hour=int(working_hours[0].hour_from),
                                minute=int((working_hours[0].hour_from % 1) * 60),
                                second=0
                            )

                            # Convert expected start time to employee's time zone
                            attendance_checkin_aware = pytz.utc.localize(attendance.check_in).astimezone(user_tz) if attendance.check_in else None
                            attendance_checkin_aware = attendance_checkin_aware.strftime('%Y-%m-%d %H:%M:%S')
                            attendance_checkin_aware = datetime.strptime(attendance_checkin_aware, '%Y-%m-%d %H:%M:%S')

                            # Calculate check-in delay
                            if attendance_checkin_aware and attendance_checkin_aware > expected_start_time:
                                checkin_delay = (attendance_checkin_aware - expected_start_time).total_seconds() / 3600.0
                                # Subtract the allowed late coming minutes from the check-in delay
                                if allow_late_coming_minutes:
                                    allow_late_coming_minutes = allow_late_coming_minutes / 60.0
                                    delay_checkin = checkin_delay - allow_late_coming_minutes
                                    # Only apply the check-in delay if the delay is greater than the allowed late coming time
                                    if delay_checkin > 0:
                                        total_checkin_delay += checkin_delay
                                else:
                                    total_checkin_delay += checkin_delay


                            # Calculate expected end time
                            expected_end_time = attendance.check_out.replace(
                                hour=int(working_hours[-1].hour_to),
                                minute=int((working_hours[-1].hour_to % 1) * 60),
                                second=0
                            )

                            # Convert expected end time to employee's time zone
                            attendance_checkout_aware = pytz.utc.localize(attendance.check_out).astimezone(user_tz) if attendance.check_out else None
                            attendance_checkout_aware = attendance_checkout_aware.strftime('%Y-%m-%d %H:%M:%S')
                            attendance_checkout_aware = datetime.strptime(attendance_checkout_aware, '%Y-%m-%d %H:%M:%S')
                            # Calculate check-out delay
                            if attendance_checkout_aware and attendance_checkout_aware < expected_end_time:
                                total_checkout_delay += (expected_end_time - attendance_checkout_aware).total_seconds() / 3600.0

          
            # Cap actual worked hours to total required hours
            actual_worked_hours = min(actual_worked_hours, total_required_hours)
            #one_day_actual_worked_hours = resource_calendar.hours_per_day or 1
            # Calculate hourly rate
            #hourly_rate = contract.wage / total_required_hours
            #hourly_rate = contract.wage / 22 / 9
            hourly_rate = contract.wage / total_working_days_per_month / total_working_hours
            # Calculate attendance deduction
            attendance_deduction = hourly_rate * (total_required_hours - actual_worked_hours)

            # Calculate delay deduction
            delay_hours = total_checkin_delay + total_checkout_delay
            delay_deduction = delay_hours * hourly_rate

            # Combine deductions
            total_deduction = attendance_deduction + delay_deduction

            # Return the result (total deduction as a negative value)
            entry.hourly_rate = hourly_rate
            entry.total_delay_hours = delay_hours
            entry.total_checkin_delay = total_checkin_delay
            entry.total_checkout_delay = total_checkout_delay
            entry.attendance_deduction = delay_deduction
