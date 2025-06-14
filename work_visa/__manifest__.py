{
    'name': "Work Visa",
    'version': "17.0.0.1",
    'summary': "This module will help you to Work Visa",
    'category': 'Work Visa',
    'description': """ Work Visa """,
    'author': "Sitaram",
    'website': "https://sitaramsolutions.in",
    'depends': ['base','hr'],
    'data': [
        'security/ir.model.access.csv',
        'views/documents_of_company_view.xml',
        'views/employee_details_view.xml',
        'views/work_permit_details_view.xml',
        'views/work_visa_details_view.xml',
        'views/procedures_after_arrival_view.xml',
        'views/hr_employee_view.xml'
    ],
    'demo': [],
    "license": "OPL-1",
    'installable': True,
    'auto_install': False,

}
