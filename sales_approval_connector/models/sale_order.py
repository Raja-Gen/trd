from odoo import fields, models, _ , api


class SaleOrder(models.Model):
    _inherit = 'sale.order'
    """Class inherited for adding extra fields and methods"""
    state = fields.Selection(
        selection_add=[('approve', 'To Approve'), ('approved', 'Approved'),
                       ('sale',), ])
    is_approved = fields.Boolean(string='Approved', default=False)

    is_approval_allowed = fields.Boolean(
        compute="_compute_is_approval_allowed",
        string="Can Approve",
        store=False
    )

    approval_history_ids = fields.One2many(
        'sale.approval.history',
        'sale_order_id',
        string="Approval History"
    )

    # this method is used to allow direst approve from sale order form

    @api.depends()
    def _compute_is_approval_allowed(self):
        for order in self:
            approval = self.env['approval.request'].search([
                ('order_id', '=', order.id),
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
            ('order_id', '=', self.id),
            ('request_status', 'not in', ('refused', 'cancel')),
        ], order='id desc', limit=1)
        if not approval_request:
            return
        approval_request.action_approve()
        history = self.env['sale.approval.history'].sudo().search([
            ('sale_order_id', '=', self.id),
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
            ('order_id', '=', self.id),
            ('request_status', 'not in', ('refused', 'cancel')),
        ], order='id desc', limit=1)
        if not approval_request:
            return
        approval_request.action_refuse()
        history = self.env['sale.approval.history'].sudo().search([
            ('sale_order_id', '=', self.id),
            ('user_id', '=', user.id),
            ('action', '=', 'requested')
        ], limit=1)
        if history:
            history.sudo().write({
                'action': 'rejected',
                'note': 'Rejected by user',
                'date': fields.Datetime.now(),
            })
       

    


    def action_draft(self):
        """Reset to draft must clear the previous approval cycle so a resubmission
        starts clean: drop the old approval.request (otherwise the form keeps
        targeting the stale rejected one) and reset the approved flag. The rejected
        approval.history rows are kept on purpose for audit."""
        res = super().action_draft()
        for order in self:
            old_requests = self.env['approval.request'].sudo().search([
                ('order_id', '=', order.id),
            ])
            if old_requests:
                old_requests.unlink()
            if order.is_approved:
                order.is_approved = False
        return res

    def _confirmation_error_message(self):
        for order in self:
            if order.state not in {'draft', 'sent', 'approve', 'approved'}:
                return _("Some orders are not in a state that allows confirmation.")
        return False
    def action_confirm(self):
        """Method is used to confirm the order"""
        if not self:
            return super().action_confirm()

        approval = self.env['approval.category'].search([('approval_type', '=', 'sale')], limit=1)
        if not approval:
            return super().action_confirm()

        orders_requiring_approval = self.filtered(lambda o: not o.is_approved)
        orders_not_requiring_approval = self.filtered(lambda o: o.is_approved)

        if orders_requiring_approval:
            for order in orders_requiring_approval:
                if approval.approver_ids:
                    history_vals = []
                    for approver in approval.approver_ids:
                        history_vals.append({
                            'sale_order_id': order.id,
                            'user_id': approver.user_id.id,
                            'action': 'requested',
                            'note': 'Approval required from this user',
                        })
                    self.env['sale.approval.history'].sudo().create(history_vals)

                self.env['approval.request'].create({
                    'name': order.name,
                    'request_owner_id': order.user_id.id,
                    'category_id': approval.id,
                    'date_start': fields.Datetime.now(),
                    'date_end': fields.Datetime.now(),
                    'order_id': order.id,
                }).action_confirm()
                approver_names = ", ".join(approval.approver_ids.mapped("user_id.name"))
                order.message_post(
                    body=_("%s created a request for approval for %s") % (self.env.user.name, order.name),
                    message_type="comment",
                )
                # Change state
                order.write({"state": "approve"})

                # Post approver info message
                order.message_post(
                    body=_("Approval request created. This Sale order will be reviewed by: %s") % approver_names,
                    subtype_xmlid="mail.mt_comment",
                    message_type="comment",
                )
    
        if orders_not_requiring_approval:
            orders_not_requiring_approval.write({'state': 'draft'})
            return super(SaleOrder, orders_not_requiring_approval).action_confirm()

        return True
