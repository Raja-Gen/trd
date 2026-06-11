# -*- coding: utf-8 -*-
{
    "name": "MS Product Brand Management",
    "version": "19.0.1.0.0",
    "summary": "Manage product brands and link them to products.",
    "description": """
        This module introduces product brand management.
        - Configure product brands with names, logos, and company association.
        - Assign brands to product templates and variants.
        - Multi-company support for brands.
    """,
    "category": "Inventory/Inventory",
    "author": "MicroSolutions, Kuwait",
    "website": "https://www.mskuwait.com",
    "depends": ["base", "product", "mail", "stock", "sale"],
    "data": [
        "security/ir.model.access.csv",
        "security/product_brand_security.xml",
        "views/product_brand_views.xml",
        "views/product_template_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
    "license": "LGPL-3",
}
