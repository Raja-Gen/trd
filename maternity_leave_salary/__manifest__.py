# -*- coding: utf-8 -*-

{
    'name': 'Maternity Leave Salary Rules',
    'version': '17.0',
    'summary': 'Handle salary rules for maternity leave',
    'description': """
This module provides salary rules for maternity leave, ensuring:
- 70 days of fully paid maternity leave.
- Unpaid leave after the fully paid period.
    """,
    'author': 'Mskuwait',
    'depends': ['hr_payroll', 'hr_holidays'],
    'data': [
        'views/res_config_settings_view.xml',
        'views/hr_holidays_views.xml',
        'data/salary_rule_data.xml',
    ],
    'installable': True,
    'application': False,
}

