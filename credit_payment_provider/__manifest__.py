{
    'name': 'credit_payment_provider',
    'version': '1.0',
    'category': 'Accounting/Payment',
    'summary': 'credit payment provider',
    'description': 'Custom integration for credit payment provider.',
    'author': 'Your Name',
    'depends': ['payment', 'sale', 'website_sale'],
    'data': [
        'data/payment_provider_data.xml',
        'views/payment_provider_views.xml',
        'views/payment_status_template.xml',
        'views/payment_template.xml',
        'views/res_partner_views.xml',
        'views/website_payment_template.xml'
    ],
    'assets': {
        'web.assets_frontend': [
            'credit_payment_provider/static/src/js/**/*',
        ],
    },
    'installable': True,
    'application': False,
}
