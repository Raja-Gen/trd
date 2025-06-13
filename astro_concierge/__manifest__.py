# -*- coding: utf-8 -*-
{
    'name': 'Astro Concierge',
    'version': '1.0',
    'summary': 'Concierge Service Management for VIP and Family Office Requests',
    'description': """
Custom Concierge Request & Feedback Management
- Priority & Confidential Tracking
- Task Assignment
- SLA Alerts
- Satisfaction Feedback
""",
    'category': 'Services/Concierge',
    'author': 'Micro Solutions, Kuwait',
    'website': 'https://mskuwait.com',
    'license': 'LGPL-3',
    'depends': ['base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/concierge_views.xml',
        'views/concierge_feedback_views.xml',
        'data/concierge_sequence.xml',
        'data/mail_template.xml',
        'data/ir_cron_data.xml'
    ],
    'application': True,
    'installable': True,
    'auto_install': False,
    'assets': {},
}
