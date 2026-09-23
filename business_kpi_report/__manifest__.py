# -*- coding: utf-8 -*-
# Part of Atharva System. See LICENSE file for full copyright and licensing details.

{
    'name': 'Business KPI Daily Reports',
    'version': '19.0.1.0.0',
    'category': 'Tools',
    'summary': """Automatically send daily business performance reports via Email and SMS.
    daily business report,
    scheduled report,
    automated business report,
    stock report,
    purchase report,
    sales report,
    automated daily email report,
    advanced report,
    direct report notification,
    daily report in sms,
    business kpi
    """,
    'description': """
    Business KPI Daily Reports for Odoo provides automated daily business reports including daily sales reports, sales value summaries, delivered orders, new website orders, and refund reports.

    The module sends scheduled management reports via Email and SMS, helping business owners and managers track business KPIs and sales performance without logging into Odoo.

    Ideal for executives who need daily business insights, sales analytics, and operational summaries delivered automatically.
    """,
    'author': 'Atharva System',
     'website': 'https://www.atharvasystem.com/odoo-development',
    'support': 'support@atharvasystem.com',
    'price': 34.00 ,
    'currency': 'EUR',
    'license' : 'OPL-1',
    'depends': [
        'base',
        'mail',
        'sms',
        'sale_management',
        'stock',
        'website_sale',
        'account',
        'payment',
        'point_of_sale',
        'purchase',
    ],
    'data': [
        'security/ir.model.access.csv',
        'data/kpi_category.xml',
        'data/kpi_data.xml',
        'data/ir_cron.xml',
        'data/mail_template.xml',
        'data/sms_template.xml',
        'views/as_kpi_view.xml',
        'views/res_config_settings_view.xml',
    ],
    'images': ["static/description/banner.png"],
    'installable': True,
    'application': False,
    'auto_install': False,
    'uninstall_hook': 'uninstall_hook',
}
