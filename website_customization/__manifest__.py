# -*- coding: utf-8 -*-
{
    "name": "Website Customization",
    "version": "17.0",
    "category": "Website",
    "summary": "Customize the website layout and design",
    "depends": ["website", "website_sale","stock","sale","sale_management"],
    "data": [
        "views/product_template.xml",
        "views/website_template_views.xml",
        "data/abandoned_cart_items.xml",
        "data/cart_email_template.xml"
    ],
    "license": "LGPL-3",
    "installable": True,
    "application": False,
}
