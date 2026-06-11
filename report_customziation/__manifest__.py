# -*- coding: utf-8 -*-
{
    "name": "MS Report Customization",
    "version": "19.0.1.0.0",
    "summary": "report customization.",
    "description": """
            Report customization for Invoice, Sale Order, and Delivery Slip.
    """,
    "category": "Sale/Stock/Accounting",
    "author": "MicroSolutions, Kuwait",
    "website": "https://www.mskuwait.com",
    "depends": ["base", "account", "sale", "stock", "sale_stock"],
    "data": [
        'views/invoice_customization.xml',
        'views/sale_order.xml',
        'views/delivery_slip.xml',
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
    "license": "LGPL-3",
}
