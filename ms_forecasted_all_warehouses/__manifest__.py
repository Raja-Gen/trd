# -*- coding: utf-8 -*-
{
    "name": "Forecasted Report: All Warehouses",
    "version": "19.0.1.0.0",
    "summary": "Adds an \"All Warehouses\" option to the Forecasted Report warehouse filter.",
    "description": """
Forecasted Report: All Warehouses
=================================

The Forecasted Report shows one warehouse at a time. This adds an "All
Warehouses" entry at the top of that warehouse dropdown, which reports the
combined figures for every warehouse the user can currently see.

The standard per-warehouse behaviour is untouched: the report still opens on a
single warehouse and only aggregates when the new entry is picked.
    """,
    "category": "Inventory/Inventory",
    "author": "MicroSolutions, Kuwait",
    "website": "https://www.mskuwait.com",
    "depends": ["stock"],
    "assets": {
        "web.assets_backend": [
            "ms_forecasted_all_warehouses/static/src/forecasted_all_warehouses.js",
        ],
        "web.assets_tests": [
            "ms_forecasted_all_warehouses/static/tests/tours/all_warehouses_tour.js",
        ],
    },
    "installable": True,
    "application": False,
    "auto_install": False,
    "license": "LGPL-3",
}
