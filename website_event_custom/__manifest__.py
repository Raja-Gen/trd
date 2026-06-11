# -*- coding: utf-8 -*-
{
    'name': 'Website Event Custom - TechSafe',
    'version': '19.0.1.0.0',
    'category': 'Marketing/Events',
    'summary': 'Custom event registration approval workflow for TechSafe',
    'description': """
        Customizes website event registration:
        - Website registrations are created in draft (Unconfirmed) state
        - Admin can review and approve registrations
        - Shows a thank-you message instead of ticket download
    """,
    'depends': ['website_event_sale'],
    'data': [
        'views/registration_thankyou.xml',
        'views/event_registration_views.xml',
    ],
    'installable': True,
    'auto_install': False,
    'license': 'LGPL-3',
}
