import firebase_admin
from firebase_admin import credentials, messaging,get_app
import json
import base64
from odoo import models

class HrExpenseSheet(models.Model):
    _inherit = 'hr.expense.sheet'

    def action_approve_expense_sheets(self):
        res = super().action_approve_expense_sheets()


        if firebase_admin._apps:
            apps = list(firebase_admin._apps.values())
            for app in apps:
                firebase_admin.delete_app(app)
        if not firebase_admin._apps:
            ICPSudo = self.env['ir.config_parameter'].sudo()
            json_file = ICPSudo.get_param('tis_firebase_fcm.firebase_json')
            if json_file:
                json_file = base64.b64decode(json_file)
                json_object = json.loads(json_file)
                cred = credentials.Certificate(json_object)
                firebase_admin.initialize_app(cred, name=cred.project_id)
                for expense in self:
                    employee = expense.employee_id
                    if employee:
                        token = employee.user_id.user_device_id
                    else:
                        token = employee.user_device_id
                    if token:
                        firebase_app = get_app(cred.project_id)
                        message = messaging.MulticastMessage(tokens=[token],
                                                             notification=messaging.Notification(
                                                                 title="Expense Approved",
                                                                 body="Your expense '%s' of amount %s has been approved." % (
                                                                     expense.name,
                                                                     expense.total_amount,
                                                                 )
                                                             ),
                                                             data={
                                                                 "screen": "expense_screen",
                                                                 "notification_type": "expense_approval",
                                                                 "id": str(expense.id),
                                                                 "order_date": expense.create_date.strftime("%Y-%m-%dT%H:%M:%SZ")
                                                             }
                                                             )
                        response = messaging.send_each_for_multicast(message, app=firebase_app)
                        self.env['push.notification'].create({
                            'user_id': employee.user_id.id,
                            'employee_id': employee.id,
                            'type': 'notification',
                            'title': 'Expense Approved',
                            'description': "Your expense '%s' of amount %s has been approved." % (
                                expense.name,
                                expense.total_amount
                            ),
                            'status_description': "success count -" + str(
                                response.success_count) + " failed count -" + str(
                                response.failure_count)
                        })
        return res

    def action_refuse_expense_sheets(self):
        res = super().action_refuse_expense_sheets()
        if firebase_admin._apps:
            apps = list(firebase_admin._apps.values())
            for app in apps:
                firebase_admin.delete_app(app)
        if not firebase_admin._apps:
            ICPSudo = self.env['ir.config_parameter'].sudo()
            json_file = ICPSudo.get_param('tis_firebase_fcm.firebase_json')
            if json_file:
                json_file = base64.b64decode(json_file)
                json_object = json.loads(json_file)
                cred = credentials.Certificate(json_object)
                firebase_admin.initialize_app(cred, name=cred.project_id)
                for expense in self:
                    employee = expense.employee_id
                    if employee.user_id:
                        token = employee.user_id.user_device_id
                    else:
                        token = employee.user_device_id
                    if token:
                        firebase_app = get_app(cred.project_id)
                        message = messaging.MulticastMessage(tokens=[token],
                                                             notification=messaging.Notification(
                                                                 title="Expense Refused",
                                                                 body="Your expense '%s' of amount %s has been refused." % (
                                                                     expense.name,
                                                                     expense.total_amount,
                                                                 ),
                                                                 data={
                                                                     "screen": "expense_screen",
                                                                     "notification_type": "expense_reject",
                                                                     "id": str(expense.id),
                                                                     "order_date": expense.create_date.strftime("%Y-%m-%dT%H:%M:%SZ")
                                                                 }
                                                             )
                                                             )
                        response = messaging.send_each_for_multicast(message, app=firebase_app)
                        self.env['push.notification'].create({
                            'user_id': employee.user_id.id,
                            'employee_id': employee.id,
                            'type': 'notification',
                            'title': 'Expense Refused',
                            'description': "Your expense '%s' of amount %s has been refused." % (
                                expense.name,
                                expense.total_amount
                            ),
                            'status_description': "success count -" + str(
                                response.success_count) + " failed count -" + str(
                                response.failure_count)
                        })
        return res