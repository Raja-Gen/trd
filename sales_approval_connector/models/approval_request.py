from odoo import fields, models, _


class ApprovalRequest(models.Model):
    _inherit = 'approval.request'

    """Class inherit for the approval request button in the form"""

    order_id = fields.Many2one('sale.order', string='Document',
                               help="Connection id for the sale order")
                               


    def action_approve(self, approver=None):
        """This method is used to confirm the order Approval"""
        res = super().action_approve(approver)
        if self.order_id:
            self.order_id.message_post(
                body=_("%s approved this Sale Order.") % self.env.user.name,
                message_type="comment"
            )  
        for order in self.order_id:
            approve_status = self.request_status
            if approve_status == "approved":
                order.write({'state': 'approved', 'is_approved': True})
                order.message_post(
                    body=_('All approvers approved — This order is now confirmed'),
                    message_type='comment')
                order.action_confirm()
        return res

    def action_refuse(self, approver=None):
        """This method is used to reject the approval request"""
        res = super().action_refuse(approver)
        if self.order_id:
            self.order_id._action_cancel()
            self.order_id.message_post(
                body=_("Approval request rejected — sale order cancelled."),
                message_type='comment'
            )
        return res
    
    def action_confirm(self):
        for request in self:
            if request.approval_type == 'sale':
                if request.order_id and request.order_id.order_line:
                    if not request.product_line_ids:
                        request.product_line_ids = [
                            (0, 0, {
                                'product_id': line.product_id.id,
                                'quantity': line.product_uom_qty,
                                'product_uom_id': line.product_uom_id.id,
                                'description': line.name,
                            })
                            for line in request.order_id.order_line
                            if not line.display_type and line.product_id
                        ]

            super(ApprovalRequest, request).action_confirm()


