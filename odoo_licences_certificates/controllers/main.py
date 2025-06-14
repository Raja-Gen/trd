# -*- coding: utf-8 -*-

# Part of Probuse Consulting Service Pvt Ltd.
# See LICENSE file for full copyright and licensing details.

# from collections import OrderedDict
# import werkzeug
from odoo.osv.expression import OR
# import base64
from odoo import http, _
from odoo.http import request
from odoo import models,registry, SUPERUSER_ID
from collections import OrderedDict
from odoo.addons.portal.controllers.portal import CustomerPortal, pager as portal_pager


class CustomerPortal(CustomerPortal):

    def _prepare_home_portal_values(self, counters):
        values = super()._prepare_home_portal_values(counters)
        if 'certificate_count' in counters:
            certificates = request.env['record.certificate']
            partner = request.env.user.partner_id
            certificate_count = certificates.sudo().search_count([
                ('certificate_type','=','customer/supplier/contact'),
                ('partner_id', 'child_of', [partner.commercial_partner_id.id])
              ])
            values['certificate_count'] = certificate_count
        if 'licences_count' in counters:
            licences_total = request.env['record.licences']
            partner = request.env.user.partner_id
            licences_count = licences_total.sudo().search_count([
                ('certificate_type','=','customer/supplier/contact'),
                ('partner_id', 'child_of', [partner.commercial_partner_id.id])
              ])
            values['licences_count'] = licences_count
        return values

    def _prepare_portal_layout_values(self):
        values = super(CustomerPortal, self)._prepare_portal_layout_values()
        certificates = request.env['record.certificate']
        licences_total = request.env['record.licences']
        partner = request.env.user.partner_id
        certificate_count = certificates.sudo().search_count([
            ('certificate_type','=','customer/supplier/contact'),
            ('partner_id', 'child_of', [partner.commercial_partner_id.id])
          ])
        licences_count = licences_total.sudo().search_count([
            ('certificate_type','=','customer/supplier/contact'),
            ('partner_id', 'child_of', [partner.commercial_partner_id.id])
          ])
        values.update({
        'certificate_count': certificate_count,
        'licences_count':licences_count
        })
        
        return values


    @http.route(['/licences/record','/licences/record/page/<int:page>'],type='http', auth="public", website=True)
    def licences_record_add(self, page=1,sortby=None,search=None,filterby=None, search_in='content',**kw):
        values = self._prepare_portal_layout_values()
        licences = request.env['record.certificate']
        partner = request.env.user.partner_id
        domain = [('certificate_type','=','customer/supplier/contact'),('partner_id', 'child_of', [partner.commercial_partner_id.id])]
        licences_count = licences.search_count(domain)
        searchbar_sortings = {
            'date': {'label': _('Newest'), 'order': 'start_date desc'},
            'Expire date': {'label': _('Expire Date'), 'order': 'end_date desc'},
            'name': {'label': _('Name'), 'order': 'name asc'},
        }
        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
        }
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']
        if not filterby:
            filterby = 'all'
        pager = portal_pager(
            url="/licences/record",
            url_args={'sortby': sortby, 'filterby': filterby, 'search_in': search_in, 'search': search},
            total=licences_count,
            page=page,
            step=self._items_per_page
        )
        searchbar_inputs = {
            'customer': {'input': 'all', 'label': _('Search in Name')},
            'all': {'input': 'all', 'label': _('Search in  Number')},
        }
        if search and search_in:
            search_domain = []
            if search_in in ('content', 'all'):
                search_domain = OR([search_domain, [('name', 'ilike', search)]])
            if search_in in ('customer', 'all'):
                search_domain = OR([search_domain, [('number', 'ilike', search)]])
            domain += search_domain
        
        licences_request = licences.sudo().search(domain,order=order,limit=self._items_per_page, offset=pager['offset'])
        values.update({
            'licences_request': licences_request,
            'page_name': 'certificate',
            'default_url': '/licences/record',
            'pager': pager,
            'searchbar_sortings':searchbar_sortings,
            'search_in': search_in,
            'searchbar_inputs': searchbar_inputs,
            'sortby': sortby,
            'filterby': filterby,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
        })
        return request.render("odoo_licences_certificates.record_licences_view",values)

    @http.route(['/licences/record/<int:licences_id>'], type='http', auth="public", website=True)
    def licences_record(self, licences_id=None,**kw):
        licences_obj = http.request.env['record.certificate'].sudo().browse(licences_id)
        vals ={
            'licences':licences_obj,
        }
        return request.render("odoo_licences_certificates.display_licences_request_from",vals)

    @http.route(['/licences/record/history','/licences/record/history/page/<int:page>'],type='http', auth="public", website=True)
    def licences_record_history(self, page=1,sortby=None,search=None,filterby=None, search_in='content',**kw):
        values = self._prepare_portal_layout_values()
        licences_history = request.env['record.licences']
        partner = request.env.user.partner_id
        domain = [('certificate_type','=','customer/supplier/contact'),('partner_id', 'child_of', [partner.commercial_partner_id.id])]
        licences_count = licences_history.search_count(domain)
        searchbar_sortings = {
            'date': {'label': _('Newest'), 'order': 'start_date desc'},
            'Expire date': {'label': _('Expire Date'), 'order': 'end_date desc'},
            'name': {'label': _('Name'), 'order': 'name asc'},
        }
        searchbar_filters = {
            'all': {'label': _('All'), 'domain': []},
        }
        if not sortby:
            sortby = 'date'
        order = searchbar_sortings[sortby]['order']
        if not filterby:
            filterby = 'all'
        pager = portal_pager(
            url="/licences/record/history",
            url_args={'sortby': sortby, 'filterby': filterby, 'search_in': search_in, 'search': search},
            total=licences_count,
            page=page,
            step=self._items_per_page
        )
        searchbar_inputs = {
            'customer': {'input': 'all', 'label': _('Search in Name')},
            'all': {'input': 'all', 'label': _('Search in  Number')},
        }
        if search and search_in:
            search_domain = []
            if search_in in ('content', 'all'):
                search_domain = OR([search_domain, [('name', 'ilike', search)]])
            if search_in in ('customer', 'all'):
                search_domain = OR([search_domain, [('number', 'ilike', search)]])
            domain += search_domain

        request_history = licences_history.sudo().search(domain,order=order,limit=self._items_per_page, offset=pager['offset'])
        values.update({
            'request_history': request_history,
            'page_name': 'licences',
            'default_url': '/licences/record/history',
            'pager': pager,
            'searchbar_sortings':searchbar_sortings,
            'sortby': sortby,
            'filterby': filterby,
            'search_in': search_in,
            'searchbar_inputs': searchbar_inputs,
            'searchbar_filters': OrderedDict(sorted(searchbar_filters.items())),
        })
        return request.render("odoo_licences_certificates.record_licences_tree_view",values)

    @http.route(['/licences/record/history<int:licences_history_id>'], type='http', auth="public", website=True)
    def licences_record_history_add(self, licences_history_id=None,**kw):
        licences_history_obj = http.request.env['record.licences'].sudo().browse(licences_history_id)
        vals ={
            'licences_history_obj':licences_history_obj,
        }
        return request.render("odoo_licences_certificates.display_licences_request_history_from",vals)
        
# vim:expandtab:smartindent:tabstop=4:softtabstop=4:shiftwidth=4:
