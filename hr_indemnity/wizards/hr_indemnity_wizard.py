# -*- coding: utf-8 -*-
import calendar
from datetime import datetime

from odoo import api, fields, models
from odoo.exceptions import UserError
from odoo.tools.float_utils import float_round


class HrIndemnityWizard(models.TransientModel):
    _name = "hr.indemnity.wizard"

    contract_id = fields.Many2one("hr.contract")
    currency_id = fields.Many2one("res.currency", string="Currency")

    serive_start_date = fields.Date(string="Serive Start", required=True)
    serive_end_date = fields.Date(string="Serive End", required=True)

    termination_type = fields.Selection(
        [
            ("employer", "Employer-Initiated"),
            ("resignation", "Employee-Initiated"),
        ],
        string="Termination Type",
        required=True,
    )

    no_of_days = fields.Integer(
        string="Working Days", default=26, readonly=False
    )
    total_indemnity_days = fields.Integer(
        string="Total Indemnity", compute="_compute_indemnity", readonly=False
    )

    tenure_years = fields.Float(
        string="Tenure Years", compute="_compute_indemnity", required=True
    )
    indemnity_amount = fields.Monetary(
        string="Indemnity Amount",
        compute="_compute_indemnity",
        digits=(8, 3),
        readonly=False,
    )

    salary_per_month = fields.Monetary(
        string="Salary per Month",
        compute="_compute_indemnity",
        digits=(8, 3),
    )

    indemnity_start_year = fields.Integer(
        default=lambda self: self.env["ir.config_parameter"]
        .sudo()
        .get_param("hr_indemnity.indemnity_start_year"),
        readonly=True,
    )

    @api.depends(
        "termination_type",
        "serive_start_date",
        "serive_end_date",
        "no_of_days",
        "total_indemnity_days",
    )
    def _compute_indemnity(self):
        """
        Calculates indemnity amount based on tenure years, termination type, wage type, and
        other parameters.
        """
        Config = self.env["ir.config_parameter"].sudo()
        indemnity_year = int(
            Config.get_param("hr_indemnity.indemnity_start_year")
        )
        wage_type = self.contract_id.wage_type

        indemnity_days = 0
        wage_per_month = 0

        for rec in self:
            # Calculating the indemnity days based on the tenure years and a
            # specific indemnity start year. Here's a breakdown of how it works:
            # For the first 5 years of service:
            #     - Indemnity = (15 days of salary per year) × (number of years up to 5 years)
            # For service beyond 5 years:
            #     - Indemnity for the first 5 years = 75 days of salary
            #     - Indemnity for subsequent years = (monthly salary per year) × (number of years beyond 5 years)
            tenure_years = 0

            if rec.serive_end_date and rec.serive_start_date:
                difference = rec.serive_end_date - rec.serive_start_date
                total_days = difference.days
                tenure_years = float_round(
                    total_days / 365, precision_digits=3
                )

            rec.tenure_years = tenure_years

            if (
                indemnity_year
                and rec.tenure_years
                and rec.tenure_years > indemnity_year
            ):
                indemnity_days = (
                    (15 * rec.tenure_years)
                    if rec.tenure_years <= 5
                    else ((15 * 5) + (rec.no_of_days * (rec.tenure_years - 5)))
                )

            # Adjusting the `indemnity_days` for `termination_type` = 'resignation' according to `tenure_years`
            # 1. For service between 3 and 5 years: The employee is entitled to 50% of the indemnity
            # 2. For service between 5 and 10 years: The employee is entitled to 2/3 of the indemnity
            # 3. For service beyond 10 years: The employee is entitled to full indemnity
            if indemnity_days and rec.termination_type == "resignation":
                indemnity_days = (
                    indemnity_days / 2
                    if rec.tenure_years < 5
                    else indemnity_days * (2 / 3)
                    if rec.tenure_years <= 10
                    else indemnity_days
                )

            # Calculating the wage per day based on the `wage_type` specified in the contract.
            if wage_type == "monthly":
                wage_per_month = rec.contract_id.wage
            if wage_type == "hourly":
                wage_per_month = (
                    rec.contract_id.resource_calendar_id.hours_per_day
                    * rec.contract_id.hourly_wage
                    * rec.no_of_days
                )

            indemnity_days = (
                indemnity_days
                if (indemnity_days / rec.no_of_days) <= 18
                else (18 * rec.no_of_days)
            )

            rec.total_indemnity_days = indemnity_days
            rec.salary_per_month = float_round(
                wage_per_month, precision_digits=3
            )
            rec.indemnity_amount = float_round(
                ((indemnity_days / rec.no_of_days) * wage_per_month),
                precision_digits=3,
            )

    def _get_or_create_salary_rule_category(self, name):
        category = self.env["hr.salary.rule.category"].search(
            [("name", "=", name)], limit=1
        )
        if not category:
            category = self.env["hr.salary.rule.category"].create(
                {
                    "name": name,
                    "code": "EOSC",
                }
            )
        return category

    def _get_or_create_salary_rule(self, name, category_id):
        rule = self.env["hr.salary.rule"].search(
            [("name", "=", name)], limit=1
        )
        if not rule:
            rule = self.env["hr.salary.rule"].create(
                {
                    "name": name,
                    "code": name[:4].upper(),
                    "category_id": category_id,
                    "sequence": 10,
                    "condition_select": "none",
                    "amount_select": "fix",
                    "amount_fix": 0.0,
                    "struct_id": 1,
                }
            )
        return rule

    def _apply_indemnity_to_salary(self):
        employee = self.contract_id.employee_id
        if not employee:
            return

        last_salary_slip = (
            self.env["hr.payslip"]
            .sudo()
            .search(
                [
                    ("employee_id", "=", employee.id),
                    ("date_to", "<=", fields.Date.today()),
                    ("state", "not in", ["done", "paid", "cancel"]),
                ],
                order="date_to desc",
                limit=1,
            )
        )

        if last_salary_slip:
            indemnity_amount = self.indemnity_amount
            print(
                "\n\n self.indemnity_amount: ", self.indemnity_amount, "\n\n"
            )
            # Ensure salary rule category and rule exist
            category = self._get_or_create_salary_rule_category(
                "End of Service"
            )
            rule = self._get_or_create_salary_rule(
                "End of Service Indemnity", category.id
            )

            # Create or update the indemnity line
            line_vals = {
                "name": "End of Service Indemnity",
                "code": rule.code,
                "category_id": category.id,
                "sequence": 100,
                "quantity": 1,
                "rate": 100,
                "amount": indemnity_amount,
                "total": indemnity_amount,
                "salary_rule_id": rule.id,
                "currency_id": last_salary_slip.currency_id.id,
            }

            # Check if the indemnity line already exists
            existing_lines = last_salary_slip.line_ids.filtered(
                lambda l: l.code == rule.code
            )
            if existing_lines:
                existing_lines.sudo().write(line_vals)
            else:
                # Add a new indemnity line
                last_salary_slip.sudo().write(
                    {"line_ids": [(0, 0, line_vals)]}
                )
        else:
            raise UserError("No salary slip found for the employee.")

    def action_apply_indemnity_to_salary(self):
        Config = self.env["ir.config_parameter"].sudo()
        if Config.get_param("hr_indemnity.allow_employee_indemnity"):
            for rec in self:
                rec._apply_indemnity_to_salary()
        else:
            raise UserError(
                "Configure the settings to provide indemnity payments to employees by navigating to: Payroll > Settings > Accounting > Allow Indemnity."
            )
