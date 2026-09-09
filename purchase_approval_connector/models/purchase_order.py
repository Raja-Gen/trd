from odoo import fields, models, _ , api


class PurchaseOrder(models.Model):
    _inherit = 'purchase.order'

    state = fields.Selection(
        selection_add=[
            ('to_approve', 'To Approve'),
            ('approved', 'Approved'),
            ('purchase',),
        ],
        ondelete={'to_approve': 'set default', 'approved': 'set default'},
    )

    is_approved = fields.Boolean(string='Approved', default=False)

    is_approval_allowed = fields.Boolean(
        compute="_compute_is_approval_allowed",
        string="Can Approve",
        store=False
    )

    approval_history_ids = fields.One2many(
        'purchase.approval.history',
        'purchase_order_id',
        string="Approval History"
    )

    # this method is used to allow direct approve from purchase order form

    @api.depends()
    def _compute_is_approval_allowed(self):
        """Check if logged-in user is one of the approvers"""
        for order in self:
            approval = self.env['approval.request'].search([
                ('purchase_order_id', '=', order.id),
                ('request_status', 'not in', ('refused', 'cancel')),
            ], order='id desc', limit=1)

            order.is_approval_allowed = False

            if approval:
                current_pending_approver = approval.approver_ids.filtered(lambda a: a.status == "pending")
                if self.env.user.id in current_pending_approver.user_id.ids:
                    order.is_approval_allowed = True

    def action_direct_approve(self):
        self.ensure_one()
        user = self.env.user

        approval_request = self.env['approval.request'].search([
            ('purchase_order_id', '=', self.id),
            ('request_status', 'not in', ('refused', 'cancel')),
        ], order='id desc', limit=1)
        if not approval_request:
            return
        approval_request.action_approve()
        history = self.env['purchase.approval.history'].sudo().search([
            ('purchase_order_id', '=', self.id),
            ('user_id', '=', user.id),
            ('action', '=', 'requested')
        ], limit=1)
        if history:
            history.sudo().write({
                'action': 'approved',
                'note': 'Approved by user',
                'date': fields.Datetime.now(),
            })

    def action_direct_reject(self):
        self.ensure_one()
        user = self.env.user

        approval_request = self.env['approval.request'].search([
            ('purchase_order_id', '=', self.id),
            ('request_status', 'not in', ('refused', 'cancel')),
        ], order='id desc', limit=1)
        if not approval_request:
            return
        approval_request.action_refuse()
        history = self.env['purchase.approval.history'].sudo().search([
            ('purchase_order_id', '=', self.id),
            ('user_id', '=', user.id),
            ('action', '=', 'requested')
        ], limit=1)
        if history:
            history.sudo().write({
                'action': 'rejected',
                'note': 'Rejected by user',
                'date': fields.Datetime.now(),
            })

    def button_draft(self):
        """Reset to draft must clear the previous approval cycle so a resubmission
        starts clean: drop the old approval.request (otherwise the form keeps
        targeting the stale rejected one) and reset the approved flag. The rejected
        approval.history rows are kept on purpose for audit."""
        res = super().button_draft()
        for order in self:
            old_requests = self.env['approval.request'].sudo().search([
                ('purchase_order_id', '=', order.id),
            ])
            if old_requests:
                old_requests.unlink()
            if order.is_approved:
                order.is_approved = False
        return res

    def button_confirm(self):
        approval = self.env['approval.category'].search(
            [('approval_type', '=', 'purchase')], limit=1
        )
        orders_to_confirm = self.env['purchase.order']
        for order in self:
            # Trigger the approval flow only when a sale category with approvers
            # exists and the order has not been approved yet.
            if approval and approval.approver_ids and not order.is_approved:
                history_vals = [{
                    'purchase_order_id': order.id,
                    'user_id': approver.user_id.id,
                    'action': 'requested',
                    'note': 'Approval required from this user',
                } for approver in approval.approver_ids]
                self.env['purchase.approval.history'].sudo().create(history_vals)

                order.write({'state': 'to_approve'})
                self.env['approval.request'].create({
                    'name': order.name,
                    'request_owner_id': order.user_id.id,
                    'category_id': approval.id,
                    'date_start': fields.Datetime.now(),
                    'date_end': fields.Datetime.now(),
                    'purchase_order_id': order.id,
                }).action_confirm()
                approver_names = ", ".join(approval.approver_ids.mapped("user_id.name"))

                order.message_post(
                    body=_("%s created an approval request for this Purchase Order.") % self.env.user.name,
                    message_type="comment"
                )
                order.message_post(
                    body=_("This Purchase Order will be reviewed by: %s") % approver_names,
                    message_type="comment"
                )
            else:
                # Already approved (or no approval configured): let the standard
                # confirmation run. Base button_confirm only processes draft/sent.
                if order.state == 'approved':
                    order.write({'state': 'draft'})
                orders_to_confirm |= order

        if orders_to_confirm:
            return super(PurchaseOrder, orders_to_confirm).button_confirm()
        return True
