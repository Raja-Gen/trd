from odoo import models, fields, _


class ApprovalRequest(models.Model):
    _inherit = 'approval.request'

    purchase_order_id = fields.Many2one(
        'purchase.order',
        string='Purchase Order',
        help="Linked Purchase Order"
    )

    def action_confirm(self):
        """ Attach PO product lines into approval request """
        for request in self:
            if request.approval_type == 'purchase':
                # If PO exists and has lines, sync them
                if request.purchase_order_id and request.purchase_order_id.order_line:
                    if not request.product_line_ids:
                        request.product_line_ids = [
                            (0, 0, {
                                'product_id': line.product_id.id,
                                'quantity': line.product_qty,
                                'product_uom_id': line.product_uom_id.id,
                                'description': line.name,
                            })
                            for line in request.purchase_order_id.order_line
                            if not line.display_type and line.product_id
                        ]
            super(ApprovalRequest, request).action_confirm()

    def _po_needs_final_approval(self):
        """High-value PO escalation: when the order total (in company currency)
        exceeds the category threshold, an extra final approver must approve
        AFTER the normal chain. Returns True only while that final approver is
        not yet part of the chain."""
        self.ensure_one()
        po = self.purchase_order_id
        category = self.category_id
        final_user = category.po_final_approver_id
        threshold = category.po_approval_threshold
        if not po or not final_user or threshold <= 0:
            return False
        # Already escalated (final approver injected) — nothing more to do.
        if self.approver_ids.filtered(lambda a: a.user_id == final_user):
            return False
        company = po.company_id or self.env.company
        amount = po.currency_id._convert(
            po.amount_total, company.currency_id, company,
            fields.Date.context_today(self),
        )
        return amount > threshold

    def _add_final_approver(self):
        """Append the configured final approver as the last (required) approver
        and notify, without confirming the PO yet."""
        self.ensure_one()
        category = self.category_id
        final_user = category.po_final_approver_id
        max_seq = max(self.approver_ids.mapped('sequence') or [10])
        self.sudo().write({
            'approver_ids': [(0, 0, {
                'user_id': final_user.id,
                'required': True,
                'sequence': max_seq + 10,
                'status': 'pending',
            })],
        })
        new_approver = self.approver_ids.filtered(
            lambda a: a.user_id == final_user
        )
        new_approver._create_activity()
        self.env['purchase.approval.history'].sudo().create({
            'purchase_order_id': self.purchase_order_id.id,
            'user_id': final_user.id,
            'action': 'requested',
            'note': 'Final approval required (order total exceeds threshold)',
        })
        self.purchase_order_id.message_post(
            body=_("Order total exceeds the approval threshold — escalated to "
                   "%s for final approval.") % final_user.name,
            message_type='comment',
        )

    def action_approve(self, approver=None):
        res = super().action_approve(approver)
        if self.purchase_order_id:
            self.purchase_order_id.message_post(
                body=_("%s approved this Purchase Order.") % self.env.user.name,
                message_type="comment"
            )
        for po in self.purchase_order_id:
            if self.request_status == "approved":
                # High-value orders need one more (final) approval after the
                # normal chain finishes — inject it instead of confirming.
                if self._po_needs_final_approval():
                    self._add_final_approver()
                    continue
                po.write({'is_approved': True, 'state': 'approved'})
                po.message_post(
                    body=_("All approvers approved — Purchase Order approved."),
                    message_type='comment'
                )
                po.button_confirm()
        return res

    def action_refuse(self, approver=None):
        res = super().action_refuse(approver)
        if self.purchase_order_id:
            self.purchase_order_id.button_cancel()
            self.purchase_order_id.message_post(
                body=_("Approval request rejected — purchase order cancelled."),
                message_type='comment'
            )
        return res
