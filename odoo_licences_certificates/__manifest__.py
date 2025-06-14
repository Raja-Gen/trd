# -*- coding: utf-8 -*-

{
    'name': 'Certificates and Licenses with Expiry Management',
    'license': 'LGPL-3',
    'author': "MicroSolutions, Kuwait",
    'website': "https://www.mskuwait.com",
    'images': ['static/description/lic_image.png'],
    'summary': 'This app allow you to manage Recycling and Waste items.',
    'description': """
        Certificates
        Certificate
        Certificates expire
        Certificates expiry
        Certificate expire
        Certificate expire date
        Certificates and Licenses with Expiry Management
        Licenses
        License
        Licenses management
        License management
        License app
        Certificate app
        expiry management
    """,
    'version': '1.0.1',
    'category': 'Services/Project',
    'depends': [
        'sale',
        'hr',
        'project',
        'website',
        'portal',
    ],
    'data': [
        'security/licences_certificate_security.xml',
        'security/ir.model.access.csv',
        'data/licences_certificate_cron.xml',
        'data/mail_templete_data.xml',
        'views/licences_certificate_type_view.xml',
        'views/licences_certificate_view.xml',
        'views/report_licences_certificate.xml',
        'views/res_partner_view.xml',
        'views/record_licences_view.xml',
        'views/record_licenes_report.xml',
        'views/record_licences_template.xml',
    ],
    'installable': True,
    'application': False,
}
