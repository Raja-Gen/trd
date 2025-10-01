{
    'name': 'Payment Cash on Delivery',
    'version': '1.0',
    'category': 'Accounting/Payment',
    'summary': 'Integrate Cash on Delivery Payment Method with Odoo 17',
    'description': 'Custom integration for Cash on Delivery payment method.',
    'author': 'Your Name',
    'depends': ['payment'],
    'data': [
        'data/payment_provider_data.xml',
        'views/payment_provider_views.xml',
        'views/payment_status_template.xml',
        'views/payment_template.xml'
    ],
    'assets': {
        'web.assets_frontend': [
            'cash_payment_provider/static/src/js/**/*',
        ],
    },
    'installable': True,
    'application': False,
}
