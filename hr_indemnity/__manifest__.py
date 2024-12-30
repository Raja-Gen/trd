# -*- coding: utf-8 -*-
{
    "name": "HR Indemnity",
    "version": "17.0",
    "category": "Human Resources",
    "summary": "Manage end-of-service indemnity calculations",
    "depends": ["hr", "hr_payroll", "hr_contract"],
    "data": [
        "security/ir.model.access.csv",
        "views/hr_contract_view.xml",
        "views/res_config_settings_view.xml",
        "wizards/hr_indemnity_wizard_views.xml",
    ],
    "license": "LGPL-3",
    "installable": True,
    "application": False,
}
