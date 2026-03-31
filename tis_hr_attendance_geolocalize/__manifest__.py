# -- coding: utf-8 --
# This module and its content is copyright of Technaureus Info Solutions Pvt. Ltd.
# - © Technaureus Info Solutions Pvt. Ltd 2022. All rights reserved.

{
    'name': 'HR Attendance Geolocalize',
    'version': '17.0.9.9',
    'category': 'Human Resources/Attendances',
    'sequence': -100,
    'summary': 'Track employee attendance',
    'author': 'Technaureus Info Solutions Pvt. Ltd.',
    'website': 'http://www.technaureus.com/',
    'price': 20,
    'currency': 'EUR',
    'license': 'Other proprietary',
    'description': "This module aims to manage employee's attendances and track location",
    'depends': ['hr_attendance', 'base_geolocalize','hr_payroll',"hr_holidays",'project_todo',"base_vat","hr_skills"],
    'external_dependencies': {
        'python': ['httpagentparser', 'geopy', 'firebase-admin', 'websocket-client'],
    },
    'data': [
        'security/ir.model.access.csv',
        'views/hr_attendance_view.xml',
        'views/res_users_views.xml',
        'views/note_note_view.xml',
        'views/hr_employee_view.xml',
        'views/push_notification_view.xml',
        'views/res_config_settings_view.xml',
        'wizard/assign_hr_wizard_view.xml',
        'data/ir_cron_views.xml',
        'views/project_task_assignment_view.xml',
    ],
    # 'assets': {
    #     'web.assets_backend': [
    #         'tis_hr_attendance_geolocalize/static/js/geo_location_finder.js',
    #         'tis_hr_attendance_geolocalize/static/js/kiosk_mode_geo_location.js',
    #     ],
    # },
    'images': ['images/main_screenshot.png'],
    'installable': True,
    'auto_install': False,
    'application': True,
}
