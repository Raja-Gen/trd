from odoo import models, fields, api

class ResPartner(models.Model):
    _inherit = 'res.partner'

    credit_limit = fields.Float(string="Credit Limit", default=0.0)
    credit_used_from_tx = fields.Float(string="Credit Used From Transactions", default=0.0)

    credit_used = fields.Float(string="Credit Used", compute="_compute_credit_used", default=0.0)

    @api.depends('credit_used_from_tx')
    def _compute_credit_used(self):
        for partner in self:
            # Sum of unpaid invoices
            moves = self.env['account.move'].search([
                ('partner_id', '=', partner.id),
                ('move_type', '=', 'out_invoice'),
                ('payment_state', '!=', 'paid')
            ])
            partner.credit_used = sum(moves.mapped('amount_total')) + partner.credit_used_from_tx

    def action_reset_credit_used(self):
        for partner in self:
            partner.credit_used = 0
            partner.credit_used_from_tx = 0