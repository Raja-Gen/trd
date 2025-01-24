# -*- coding: utf-8 -*-

from odoo import fields, models, api
from datetime import timedelta


class HrPayslipWorkedDays(models.Model):
    _inherit = "hr.payslip.worked_days"

    number_of_sick_leave_days = fields.Integer(
        string="Sick Leave Days",
        compute="_compute_sick_leave_days",
        help="The number of sick leave days taken during the payslip period.",
    )

    @api.depends(
        "payslip_id",
        "payslip_id.employee_id",
        "payslip_id.date_from",
        "payslip_id.date_to",
    )
    def _compute_sick_leave_days(self):
        for worked_day in self:
            sick_leave_days = 0.0

            # Ensure we have a sick leave type (you can replace this with your actual sick leave type ID or name)
            sick_leave_type = self.env["hr.leave.type"].search(
                [("is_sick_leave", "=", True)]
            )

            if sick_leave_type:
                # Search for validated sick leave records within the payslip period
                leave_requests = self.env["hr.leave"].search(
                    [
                        ("employee_id", "=", worked_day.payslip_id.employee_id.id),
                        (
                            "holiday_status_id",
                            "in",
                            sick_leave_type.ids,
                        ),  # Ensuring it’s sick leave
                        ("state", "=", "validate"),  # Only validated leaves,
                        ("request_date_from", "<=", worked_day.payslip_id.date_to),
                        ("request_date_to", ">=", worked_day.payslip_id.date_from),
                    ]
                )
                for leave in leave_requests:
                    week_days = [
                        int(day)
                        for day in worked_day.payslip_id.contract_id.resource_calendar_id.attendance_ids.mapped(
                            "dayofweek"
                        )
                    ]
                    if leave.date_from.date() < worked_day.payslip_id.date_from <= leave.date_to.date():
                        current_day = worked_day.payslip_id.date_from
                        while current_day <= leave.date_to.date():
                            if current_day.weekday() in week_days:
                                sick_leave_days += 1
                            current_day += timedelta(days=1)
                    elif leave.date_to.date() <= worked_day.payslip_id.date_to:
                        sick_leave_days += leave.number_of_days
                    else:
                        current_day = leave.date_from.date()
                        while current_day <= worked_day.payslip_id.date_to:
                            if current_day.weekday() in week_days:
                                sick_leave_days += 1
                            current_day += timedelta(days=1)
            worked_day.number_of_sick_leave_days = sick_leave_days
