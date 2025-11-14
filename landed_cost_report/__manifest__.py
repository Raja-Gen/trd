{
    "name": "Landed Cost Report",
    "version": '17.0.0.0',
    "summary": "Gives landed cost report",
    "description": "Provides a landed cost report for specific purchase orders.",
    "author": "Mskuwait",
    "category": "Accounting",
    "depends": ["base","purchase"],
    "data": [
        "security/ir.model.access.csv",
        "views/landed_cost_wizard_view.xml",
        "views/landed_cost_template.xml",
        "views/menu.xml",
        'views/landed_cost_report.xml',
    ],
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
