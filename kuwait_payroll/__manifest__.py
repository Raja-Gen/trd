# coding: utf-8
{
    'name': 'Kuwait-Payroll',
    'version': '17.0.0.0',
    "author": "Alkhuzam & Co. - Morison Advisory",
    'summary': 'Kuwait Payroll and End of Service rules.',
    'category': 'Human Resources/Payroll',
    'description': """
Kuwait Payroll and End of Service rules.
========================================
Configuration of hr_payroll for kuwait localization
Calculating the basic salary for the employees following the kuwait law.
Calculating the end of service and provision
Daily computation of leaves and end of service for each contracted employee.
    """,
    'depends': ['hr_contract', 'hr_payroll', 'hr_expense','hr','hr_holidays'],
    'data': [
        'security/ir.model.access.csv',
        'data/sick_leave_rule.xml',
        'wizard/eos_benefit_views.xml',
        'wizard/lad_views.xml',
        'views/hr_employee_leave_approval_views.xml',
        'views/hr_contract_views.xml',
        'views/hr_payslip_views.xml',
        'views/hr_leave_views.xml',
        'views/hr_employee_public_views.xml',
        'views/eos_views.xml'
    ],
    'license': 'OPL-1',
    "installable": True,
    'auto_install': False,
    'application':True,
    'price': 100,
    'currency': 'USD',
    'images': ['static/description/banner.gif'],
    'company': 'Alkhuzam & Co.- Morison Advisory',
    'maintainer': 'Alkhuzam & Co.- Morison Advisory',
}
