# -*- coding: utf-8 -*-
{
    'name': 'Request Document',
    'version': '17.0.1.0.4',
    'category': 'Human Resources',
    'summary': ('Employee document request management with approvals and ' 
        'alerts.'),
    'description': (
        'This module allows employees to submit document requests that are '
        'reviewed and approved by authorized users. Approvers receive ' 
        'automatic email alerts, and employees are notified of the approval '
        'or rejection. Document types are configurable, and all actions are '
        'tracked through chatter for transparency and compliance.'
    ),
    'company': 'Alhodood Technologies',
    'maintainer': 'Alhodood Technologies',
    'support': 'sales@alhodood.com',
    'website': 'https://www.alhodood.com',
    'author': 'Alhodood Technologies',
    'depends': [
        'hr', 'tis_hr_attendance_geolocalize',
    ],
    'data': [
        'security/security.xml',
        'security/ir.model.access.csv',
        'views/request_document.xml',
        'wizard/reject_reason.xml',
    ],
    'images': ['static/description/banner.gif'],
    'assets': {},
    'license': 'LGPL-3',
    'installable': True,
    'auto_install': False,
    'application': False,
}
