# -*- coding: utf-8 -*-
{
    "name": "MS Invoice Report",
    "version": "19.0.1.0.0",
    "summary": "MicroSolutions Kuwait branded customer invoice PDF.",
    "description": """
            Customer invoice PDF traced from the MicroSolutions Kuwait design
            (MS Invoice.pdf). Standalone report, shown only for the
            MicroSolutions Kuwait company.
    """,
    "category": "Accounting/Accounting",
    "author": "MicroSolutions, Kuwait",
    "website": "https://www.mskuwait.com",
    "depends": ["base", "account"],
    "data": [
        "report/paperformat.xml",
        "report/ms_invoice_styles.xml",
        "report/ms_invoice_report.xml",
        "report/report_action.xml",
        "views/res_company_views.xml",
    ],
    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": False,
    "auto_install": False,
    "license": "LGPL-3",
}
