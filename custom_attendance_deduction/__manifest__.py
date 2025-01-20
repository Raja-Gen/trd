# -*- coding: utf-8 -*-
{
    'name': 'Attendance Deduction for Payroll',
    'version': '17.0.1.0.0',
    'summary': 'Calculate and apply attendance-based deductions to employee payslips',
    'description': """
        This module calculates attendance-based deductions by evaluating 
        check-in and check-out delays and applies them to employee payslips.
    """,
    'category': 'Human Resources/Payroll',
    'author': 'mskuwait',
    'depends': ['hr_payroll', 'hr_attendance','base'],
    'data': [
        'data/salary_rule_data.xml',
        'views/hr_work_entry_type_view.xml',
        'views/res_config_settings_view.xml'
    ],
    'license': 'LGPL-3',
    'installable': True,
    'application': False,
    'auto_install': False,
}

