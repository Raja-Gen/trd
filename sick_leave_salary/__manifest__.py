# -*- coding: utf-8 -*-

{
    "name": "Sick Leave Salary Rules",
    "version": "17.0",
    "summary": "Manages sick leave salary rules in Odoo Payroll",
    "description": "Implements salary rules for sick leave with different payment structures.",
    "author": "Mskuwait",
    "category": "Human Resources",
    "depends": ["hr_payroll", "hr_holidays"],
    "data": [
        "data/salary_rule_data.xml",
        "views/hr_holidays_views.xml",
        "views/hr_work_entry_type_view.xml",
        "views/hr_salary_rule_view.xml",
    ],
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
