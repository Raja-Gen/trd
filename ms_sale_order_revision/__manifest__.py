# -*- coding: utf-8 -*-
{
    'name': 'MS Sale Order Revision Tracking',
    'version': '19.0.1.0.0',
    'summary': 'Tracks sale order line changes, logs them, and manages order revisions.',
    'description': """
Key Features:
1.  **Chatter Logs for Line Changes:**
    - When a sale order line is added, a note "Order line added: Product [Product Name]..." is logged in the sale order's chatter.
    - When a sale order line is deleted, a note "Order line deleted: Product [Product Name]..." is logged.

2.  **Order Revision Field (`order_revise`):**
    - Adds a new character field "Order Revision" to the `sale.order` model.
    - This field stores revision identifiers like R1, R2, R3, etc.

3.  **Automatic Revision Increment:**
    - The "Order Revision" field is automatically incremented (e.g., from R1 to R2) whenever:
        - A new sale order line is added.
        - An existing sale order line is removed.
        - Any field on an existing sale order line is updated.

4.  **Dynamic `display_name` Update:**
    - The `display_name` of a sale order is updated to include its current revision.
    - For example, an order "SO001" with partner "Azure Interior" at revision "R1" will display as "SO001 - Azure Interior-R1".
    - This updated display name will appear in the form view header and other areas where `display_name` is used.
    """,
    'author': 'MicroSolutions, Kuwait',
    'website': 'https://www.mskuwait.com',
    'category': 'Sales/Sales',
    'depends': ['sale_management'], # Ensures 'sale' app and its models are available
    'data': [
        'views/sale_order_views.xml',
    ],
    'installable': True,
    'application': False,
    'auto_install': False,
    'license': 'LGPL-3',
}
