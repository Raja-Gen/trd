# -*- coding: utf-8 -*-
{
    "name": "MS Customization",
    "version": "19.0.1.1.0",
    "summary": "Read-only Purchase access, CRM quotation/won stage automation, and a Trader / End User type on customers.",
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

3. Customer Type
----------------
Adds a "Customer Type" option on the contact form - Trader or End User - so a
customer can be classified while it is being created. Available on the contact
list as an optional column, and as filters and a Group By in the contact search.

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
        "views/res_partner_views.xml",
    ],
    "installable": True,
    "application": False,
    "auto_install": False,
    "license": "LGPL-3",
}
