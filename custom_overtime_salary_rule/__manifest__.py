# -*- coding: utf-8 -*-

{
    'name': 'Custom Overtime Salary Rule',
    'version': '17.0',
    'author': 'Mskuwait',
    'category': 'Human Resources',
    'summary': 'Add overtime salary rules for regular days, weekly day off, and public holidays.',
    'description': '''
        This module extends the HR Salary Rule to include custom computations for:
        - Regular overtime (1.25x hourly rate)
        - Weekly day off overtime (1.50x hourly rate)
        - Public holiday overtime (2.00x hourly rate)
        The computations are based on contract wage and input data.
    ''',
    'depends': ['hr', 'hr_payroll','custom_attendance_deduction'],
    'data': ['views/hr_work_entry_type_view.xml','data/salary_rule_data.xml'],
    'installable': True,
    'application': False,
    'auto_install': False,
}
