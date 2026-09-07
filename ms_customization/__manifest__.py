# -*- coding: utf-8 -*-
{
    "name": "MS Customization",
    "version": "19.0.1.0.0",
    "summary": "Read-only Purchase access, and CRM quotation/won stage automation.",
    "description": """
MS Customization
================

In-house customizations for MicroSolutions / Raja.

1. Purchase Read Only
---------------------
Adds a "Read Only" level to the Purchase privilege. A user with it can open the
Purchase app and view requests for quotation, purchase orders and purchase
reporting, but cannot create, edit, confirm or cancel anything.

2. CRM Quotation & Won Stage Automation
---------------------------------------
Keeps the CRM pipeline in step with the sales flow: a quotation raised for an
opportunity moves it to the Quotation stage of its own sales team, and
confirming that quotation into a sales order moves it to the Won stage of that
same team.

See README.md for the full behaviour, including what the automation
deliberately leaves alone.
    """,
    "category": "Sales",
    "author": "MicroSolutions, Kuwait",
    "website": "https://www.mskuwait.com",
    "depends": [
        # Purchase read-only
        "purchase",
        "purchase_stock",
        "stock",
        # CRM stage automation + inventory items on leads
        "crm",
        "sale_crm",
        "sale",
    ],
    "data": [
        "security/purchase_readonly_security.xml",
        # "security/crm_own_leads_security.xml",
        "security/ir.model.access.csv",
        "views/purchase_menus.xml",
        "views/purchase_order_views.xml",
        "views/crm_stage_views.xml",
        "views/crm_lead_views.xml",
        "views/stock_picking_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
    "license": "LGPL-3",
}
