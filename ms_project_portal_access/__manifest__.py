# -*- coding: utf-8 -*-
{
    "name": "MS Project Portal Access",
    "version": "19.0.1.0.0",
    "summary": "Give portal users access to individual tasks, MicroSolutions only.",
    "description": """
            Internal users pick portal users on a task; those users then open it on
            Odoo's own project sharing board and can edit it and change its status.
            Applies only to companies with the flag ticked on the company form.
    """,
    "category": "Services/Project",
    "author": "MicroSolutions, Kuwait",
    "website": "https://www.mskuwait.com",
    "depends": ["project"],
    "data": [
        "security/project_portal_security.xml",
        "views/res_company_views.xml",
        "views/project_task_views.xml",
    ],
    "assets": {
        "web.assets_tests": [
            "ms_project_portal_access/static/tests/tours/*.js",
        ],
    },
    "post_init_hook": "post_init_hook",
    "installable": True,
    "application": False,
    "auto_install": False,
    "license": "LGPL-3",
}
