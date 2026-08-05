# -*- coding: utf-8 -*-
##############################################################################
#
#    OpenERP, Open Source Management Solution
#    Copyright (C) 2015 DevIntelle Consulting Service Pvt.Ltd (<http://www.devintellecs.com>).
#
#    For Module Support : devintelle@gmail.com  or Skype : devintelle
#
##############################################################################

from odoo import api, fields, models, _
from odoo.exceptions import UserError


class PettyBulkAttachWizard(models.TransientModel):
    _name = 'petty.bulk.attach.wizard'
    _description = 'Petty Cash Bulk Attach Documents'

    line_ids = fields.One2many(
        'petty.bulk.attach.line', 'wizard_id',
        string='Documents',
    )

    def action_attach(self):
        """Attach the uploaded document(s) of every row to the row's voucher.

        Attaching writes the target voucher (adds to ``attachment_ids``), so the
        normal access rules apply automatically: a user can only attach to
        vouchers they are allowed to edit.
        """
        self.ensure_one()
        if not self.line_ids:
            raise UserError(_('Add at least one row with a voucher and its document(s).'))

        vouchers = self.env['dev.petty.voucher']
        total_files = 0
        for line in self.line_ids:
            if not line.voucher_id:
                raise UserError(_('Every row must have a petty cash voucher selected.'))
            if not line.attachment_ids:
                raise UserError(
                    _('Please add at least one document for voucher %s.')
                    % line.voucher_id.display_name
                )
            # Re-home the uploaded attachments onto the voucher and link them.
            line.attachment_ids.write({
                'res_model': 'dev.petty.voucher',
                'res_id': line.voucher_id.id,
            })
            line.voucher_id.attachment_ids = [(4, att.id) for att in line.attachment_ids]
            line.voucher_id.message_post(
                body=_('%d document(s) attached via bulk upload.') % len(line.attachment_ids)
            )
            total_files += len(line.attachment_ids)
            vouchers |= line.voucher_id

        return {
            'type': 'ir.actions.client',
            'tag': 'display_notification',
            'params': {
                'title': _('Bulk Attach Documents'),
                'message': _('%d document(s) attached to %d voucher(s).') % (
                    total_files, len(vouchers)),
                'type': 'success',
                'next': {'type': 'ir.actions.act_window_close'},
            },
        }


class PettyBulkAttachLine(models.TransientModel):
    _name = 'petty.bulk.attach.line'
    _description = 'Petty Cash Bulk Attach Line'

    wizard_id = fields.Many2one(
        'petty.bulk.attach.wizard', required=True, ondelete='cascade')
    voucher_id = fields.Many2one(
        'dev.petty.voucher', string='Petty Cash Voucher', required=True,
        domain="[('state', '!=', 'cancelled')]",
        help='Enter/select the petty cash voucher number to attach the documents to.',
    )
    attachment_ids = fields.Many2many(
        'ir.attachment',
        'petty_bulk_attach_line_att_rel', 'line_id', 'attachment_id',
        string='Documents',
    )
    attachment_count = fields.Integer(
        string='Files', compute='_compute_attachment_count')

    @api.depends('attachment_ids')
    def _compute_attachment_count(self):
        for line in self:
            line.attachment_count = len(line.attachment_ids)
