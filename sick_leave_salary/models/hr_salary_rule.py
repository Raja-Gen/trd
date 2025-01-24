from odoo import models, fields, _
from odoo.tools.safe_eval import safe_eval
import datetime
from odoo.exceptions import UserError


class HrSalaryRule(models.Model):
    _inherit = "hr.salary.rule"

    deduct_sick_leave = fields.Boolean(string="Deduct Sick Leave")
    min_days = fields.Integer(string="Min Days")
    max_days = fields.Integer(string="Max Days")

    def _compute_rule(self, localdict):
        amount, qty, rate = super()._compute_rule(localdict)
        self.ensure_one()
        localdict["localdict"] = localdict
        if self.amount_select == "percentage" and self.deduct_sick_leave:
            try:
                payslip = localdict.get("payslip", False)
                if payslip and payslip.worked_days_line_ids:
                    sick_leave_days = 0.0
                    total_working_days = 0.0
                    sick_leave_line = payslip.worked_days_line_ids.filtered(
                        lambda line: line.work_entry_type_id.is_leave
                    )
                    for line in sick_leave_line:
                        leave_lines = (
                            line.mapped("work_entry_type_id")
                            .mapped("leave_type_ids")
                            .filtered(lambda leave: leave.is_sick_leave)
                        )
                        for leave in leave_lines:
                            sick_leave_days += line.number_of_sick_leave_days
                            total_working_days = line.working_days

                    today = datetime.date.today()
                    current_year = today.year
                    start_date = datetime.date(current_year, 1, 1)
                    sick_leave_type = self.env["hr.leave.type"].search(
                        [("is_sick_leave", "=", True)], limit=1
                    )
                    current_year_past_sick_leave = self.env["hr.leave"].search(
                        [
                            ("employee_id", "=", payslip.employee_id.id),
                            (
                                "holiday_status_id",
                                "=",
                                sick_leave_type.id,
                            ),  # Ensuring it’s sick leave
                            ("state", "=", "validate"),  # Only validated leaves
                            ("request_date_to", ">=", start_date),
                            ("request_date_to", "<", payslip.date_from),
                        ]
                    )
                    current_year_past_sick_leave_days = sum(
                        current_year_past_sick_leave.mapped("number_of_days")
                    )
                    total_sick_leave_days = (
                        sick_leave_days + current_year_past_sick_leave_days
                    )
                    if self.max_days < current_year_past_sick_leave_days:
                        amount = 0.0
                        qty = 0
                        rate = 0
                    elif self.max_days < total_sick_leave_days:
                        if not isinstance(total_sick_leave_days, (float, int)):
                            return None
                        qty = (
                            self.max_days
                            - self.min_days
                            + 1
                            - (current_year_past_sick_leave_days - self.min_days + 1)
                        )
                        return (
                            float(
                                safe_eval(
                                    str(round(amount / total_working_days, 2)),
                                    localdict,
                                )
                            ),
                            float(safe_eval(str(qty), localdict)),
                            self.amount_percentage or 0.0,
                        )
                    elif self.min_days <= total_sick_leave_days < self.max_days:
                        if not isinstance(total_sick_leave_days, (float, int)):
                            return None
                        qty = total_sick_leave_days - self.min_days + 1
                        return (
                            float(
                                safe_eval(
                                    str(round(amount / total_working_days, 2)),
                                    localdict,
                                )
                            ),
                            float(safe_eval(str(qty), localdict)),
                            self.amount_percentage or 0.0,
                        )
                    else:
                        amount = 0.0
                        qty = 0
                        rate = 0
            except Exception as e:
                self._raise_error(
                    localdict, _("Wrong percentage base or quantity defined for:"), e
                )
        return amount, qty, rate
