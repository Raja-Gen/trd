# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##############################################################################

{
    'name': 'Petty Cash Management | Petty Cash Request | Petty Cash Expense',
    'version': '19.0.1.1',
    'sequence': 1,
    'category': 'Accouting',
    'description':
        """
Petty cash management odoo app designed to simplify the management of petty cash transactions.
It allows users to create and handle petty cash requests, record expenses, and manage the
approval workflow. The module includes a dashboard for an overview of all petty cash activities,
enabling users to track and monitor transactions effectively. Additionally, it provides
reporting capabilities, allowing users to print petty cash requests and expenses as PDF reports.
The module integrates with Odoo's Employees, Invoicing, and Discuss modules, ensuring a cohesive
and efficient management process. Payments can be registered and reconciled within the module,
providing a complete solution for managing petty cash in an organization.

Overall, this app ensures efficient petty cash management, improved authorization workflows,
and enhanced integration with your existing Odoo modules, streamlining financial operations and
reducing manual errors.

Odoo Petty Cash Management
Efficient Petty Cash System
Petty Cash Handling in Odoo
Odoo Petty Cash Module
Streamlined Petty Cash Management
Petty Cash Workflow in Odoo
Odoo Petty Cash Control
Petty Cash Tracking and Reporting
Odoo Petty Cash Expenses
Petty Cash Reconciliation in Odoo
Odoo Petty Cash Fund Management
Petty Cash Handling Procedures
Odoo Petty Cash Register
Petty Cash Accountability in Odoo
Odoo Petty Cash Expense Management

odoo app allow Petty Cash Management, Petty Cash Request, Petty cash expense, Petty Cash Workflow approval process, Petty Cash Request balance, Petty Cash Expense Remaing Balance, Petty Cash due balance, Petty Cash user wise allocation, Cash flow Petty Cash management in odoo

    """,
    'summary': 'petty cash management petty cash request petty cash approval workflow petty cash expense manage petty cash expenses petty cash accounting petty cash finance petty cash request petty cash fund management day to day cash operation management auto petty cash funding auto petty cash fund management odoo petty cash operational expense management',
    'depends': [
        'account',
        'mail',
        'hr',
    ],
    #removed from manifest depends account_accountant
    'external_dependencies': {},
    'data': [
        # Security
        'security/petty_cash_security.xml',
        'security/ir.model.access.csv',
        # Data
        'data/ir_sequence_data.xml',
        'data/email_templates.xml',
        'data/ir_cron_data.xml',
        'data/dashboard_cron.xml',
        # Reports
        'reports/petty_voucher_report.xml',
        'reports/petty_voucher_report_template.xml',
        'reports/petty_aging_report.xml',
        'reports/petty_aging_report_template.xml',
        # Views
        'views/dev_petty_fund_views.xml',
        'views/dev_petty_voucher_views.xml',
        'views/dev_petty_replenish_views.xml',
        'views/dashboard_views.xml',
        'views/petty_policy_views.xml',
        'views/petty_approval_matrix_views.xml',
        'views/petty_aging_views.xml',
        'views/petty_cash_menu.xml',
        # Wizard (after the menu file: the bulk-attach menuitem parents onto
        # menu_petty_cash_vouchers, which petty_cash_menu.xml defines)
        'wizard/petty_cash_reconcile_wizard_views.xml',
        'wizard/petty_bulk_attach_wizard_views.xml',
    ],
    'assets': {
        'web.assets_backend': [
            'dev_petty_cash/static/src/scss/attachment_preview_field.scss',
            'dev_petty_cash/static/src/js/attachment_preview_field.js',
            'dev_petty_cash/static/src/xml/attachment_preview_field.xml',
        ],
        'web.assets_tests': [
            'dev_petty_cash/static/tests/tours/petty_attachment_preview_tour.js',
            'dev_petty_cash/static/tests/tours/petty_bulk_approve_tour.js',
        ],
    },
    'demo': [],
    'test': [],
    'css': [],
    'qweb': [],
    'js': [],
    'images': ['images/main_screenshot.gif'],
    'installable': True,
    'application': True,
    'auto_install': False,
    
    # author and support Details =============#
    'author': 'DevIntelle Consulting Service Pvt.Ltd',
    'website': 'https://www.devintellecs.com',    
    'maintainer': 'DevIntelle Consulting Service Pvt.Ltd', 
    'support': 'devintelle@gmail.com',
    'price':59.0,
    'currency':'EUR',
    'live_test_url':'https://www.youtube.com/watch?v=UN_Umjxwpy4',
}
