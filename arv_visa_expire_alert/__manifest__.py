# -*- coding: utf-8 -*-
{
    'name': 'Visa Expiration Notification',
    'version': '17.0.1.0',
    'sequence': 1,
    'website': 'aravindu28@gmail.com',
    'category': 'Extra Tools',
    'summary': """This module serves the purpose of notifying selected Users regarding visa expiration.""",
    'description': """ This module serves the purpose of notifying selected Users regarding visa expiration. """,
    'author': 'Aravind S',
    'support': 'aravindu28@gmail.com',
    'depends': ['base', 'hr'],
    'license': 'LGPL-3',
    'data': [
        'security/ir.model.access.csv',
        'views/settings.xml',
        'views/visa.xml',
        'views/employee.xml',
        'data/cron.xml'
    ],
    'installable': True,
    'application': True,
    'auto_install': False,
    'images': ['static/description/thumbnail.gif'],
}
