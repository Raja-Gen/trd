# -*- coding: utf-8 -*-

import pdb
import pdb
import werkzeug

from odoo import http, _
from odoo.http import request
from odoo.exceptions import UserError
from odoo.addons.website_event.controllers.main import WebsiteEventController

from collections import Counter


class WebsiteEventCustomController(WebsiteEventController):

    def _create_attendees_from_registration_post(self, event, registration_data):
        """ Also try to set a visitor (from request) and
        a partner (if visitor linked to a user for example). Purpose is to gather
        as much informations as possible, notably to ease future communications.
        Also try to update visitor informations based on registration info. """
        visitor_sudo = request.env['website.visitor']._get_visitor_from_request(force_create=True)

        registrations_to_create = []
        for registration_values in registration_data:
            registration_values['event_id'] = event.id
            if not registration_values.get('partner_id') and visitor_sudo.partner_id:
                registration_values['partner_id'] = visitor_sudo.partner_id.id
            elif not registration_values.get('partner_id'):
                registration_values['partner_id'] = False if request.env.user._is_public() else request.env.user.partner_id.id

            # update registration based on visitor
            registration_values['visitor_id'] = visitor_sudo.id
            if event.company_id.name == 'TechSafe':
                registration_values['state'] = 'draft'

            registrations_to_create.append(registration_values)

        return request.env['event.registration'].sudo().create(registrations_to_create)

    @http.route(['''/event/<model("event.event"):event>/registration/confirm'''],
                type='http', auth="public", methods=['POST'], website=True)
    def registration_confirm(self, event, **post):
        """Override to redirect to thank-you page instead of ticket download page."""
        try:
            request.env['ir.http']._verify_request_recaptcha_token('website_event_registration')
        except UserError:
            raise UserError(_('Suspicious activity detected by Google reCaptcha.'))
        registrations_data = self._process_attendees_form(event, post)
        registration_tickets = Counter(
            registration['event_ticket_id'] for registration in registrations_data
        )
        event_tickets = request.env['event.event.ticket'].browse(
            list(registration_tickets.keys())
        )
        if any(
            event_ticket.seats_limited
            and event_ticket.seats_available < registration_tickets.get(event_ticket.id)
            for event_ticket in event_tickets
        ):
            return request.redirect(
                '/event/%s/register?registration_error_code=insufficient_seats' % event.id
            )
        self._create_attendees_from_registration_post(event, registrations_data)

        # Redirect to custom thank-you page instead of ticket download
        return request.redirect('/event/%s/registration/thankyou' % event.id)

    @http.route(['/event/<model("event.event"):event>/registration/thankyou'],
                type='http', auth="public", methods=['GET'], website=True, sitemap=False)
    def event_registration_thankyou(self, event, **post):
        """Display the TechSafe thank-you message after registration."""
        return request.render("website_event_custom.registration_thankyou", {
            'event': event,
        })
