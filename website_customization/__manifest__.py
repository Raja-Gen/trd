# -*- coding: utf-8 -*-
{
    "name": "Website Customization",
    "version": "19.0.1.0.0",
    "category": "Website",
    "summary": "Customize the website layout and design",
    "depends": ["website", "website_sale","stock","sale","sale_management"],
    "data": [
        "views/product_template.xml",
        "views/website_template_views.xml",
        "data/abandoned_cart_items.xml",
        "data/cart_email_template.xml",
        "data/unfreeze_stock_cron_job.xml",
        "views/sale_order_views.xml",
        "wizards/freeze_stock_views.xml",
        "security/ir.model.access.csv"
    ],
    "assets": {
        "web.assets_frontend": [
            "website_customization/static/src/js/variant_availability.js",
        ],
    },
    "license": "LGPL-3",
    "installable": True,
    "application": False,
}
