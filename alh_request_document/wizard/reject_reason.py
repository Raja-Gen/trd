# -*- coding: utf-8 -*-
#############################################################################

#    Alhodood Technologies.
#
#    Copyright (C) 2024-TODAY Alhodood Technologies(<https://www.alhodood.com>)
#    Author: Alhodood Technologies(<https://www.alhodood.com>)
#
# You can modify it under the terms of the GNU Affero General Public License
# (AGPL v3), Version 3.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU Affero General Public License (AGPL v3) for more details.
#
#    You should have received a copy of the GNU Affero General Public License
#    (AGPL v3) along with this program.
#    If not, see <http://www.gnu.org/licenses/>.
#
#############################################################################
from odoo import fields, models, api, _


class RejectionFeedback(models.TransientModel):
    _name = 'rejection.feedback.wizard'
    _description = "Rejection Feedback"

    feedback = fields.Text('Feedback')

    def action_add_feedback(self):
        request_id = self.env['document.request'].search(
            [('id',
            '=',
            self.env.context['active_id'])]
        )

        request_id.reject_reason = self.feedback
        subject = (
            "Document Request Refused: "
            f"{request_id.name}"
        )
        employee_email = request_id.employee_id.work_email or request_id.employee_id.user_id.email
        body = f"""
                    <p>Hello {request_id.employee_id.name},</p>
                    <p>Your document request has been refused.</p>
                    <p><strong>Document Name:</strong> {request_id.name}</p>
                    <p><strong>Refused Date:</strong> {fields.Datetime.now(
                        ).strftime('%Y-%m-%d %H:%M:%S'
                    )}</p>
                    <p><strong>Feedback:</strong> {self.feedback}</p>
                    <p>Best Regards,</p>
                    <p>{self.env.user.name}</p>
                """
        mail_values = {
            'subject': subject,
            'body_html': body,
            'email_to': employee_email,
            'email_from': self.env.user.email,
        }
        mail = self.env['mail.mail'].sudo().create(mail_values)
        mail.send()
        request_id.state = 'reject'
