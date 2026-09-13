# -*- coding: utf-8 -*-
{
    'name': 'MS Bank Matching Date Format',
    'version': '19.0.1.0.0',
    'summary': 'Show the full DD/MM/YYYY date on Bank Matching transactions.',
    'description': """
Bank Matching Date Format
=========================

The Bank Matching (bank reconciliation) screen hardcodes its transaction date to
a short "MMM dd" form (e.g. "Apr 14"), which hides the year. This module makes it
print the full date using the user's language date format instead (%d/%m/%Y here,
so 14/04/2026).
""",
    'category': 'Accounting/Accounting',
    'author': 'MicroSolutions',
    'depends': ['account_accountant'],
    'assets': {
        'web.assets_backend': [
            'ms_bank_matching_date_format/static/src/js/bank_rec_statement_line.js',
            'ms_bank_matching_date_format/static/src/scss/bank_matching_date.scss',
        ],
    },
    'installable': True,
    'application': False,
    'license': 'LGPL-3',
}
