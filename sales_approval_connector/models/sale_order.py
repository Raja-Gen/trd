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

    is_approval_required = fields.Boolean(
        compute="_compute_is_approval_required",
        string="Approval Required",
        help="True when an approval category with approvers is configured for "
             "this order's company. Drives which confirm button the form shows: "
             "companies with no approval set up keep the standard Confirm.",
    )

    @api.depends('company_id', 'currency_id', 'amount_total')
    def _compute_is_approval_required(self):
        for order in self:
            order.is_approval_required = bool(order._ms_approval_category())

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
    def _ms_approval_category(self):
        """The approval category that governs THIS order, or an empty recordset.

        Matched on the order's OWN company, so configuring approval for one
        company leaves every other company alone. Categories with no approvers
        are ignored: an empty one means "approval is not set up for this
        company", which must confirm normally rather than gate the order or -
        worse - park it in To Approve with nobody able to move it. That filter
        is also what keeps Odoo's own empty "Create RFQ's" category (shipped by
        approvals_purchase, sequence 80) from hijacking the lookup.

        Read in sudo on purpose: whether an order needs approval is a property
        of the order, not of which companies the person confirming happens to
        have ticked in the company switcher.
        """
        self.ensure_one()
        category = self.env['approval.category'].sudo().search([
            ('approval_type', '=', 'sale'),
            ('company_id', '=', self.company_id.id),
            ('approver_ids', '!=', False),
        ], order='sequence, id', limit=1)
        if category and not self._ms_meets_approval_threshold(category):
            return self.env['approval.category']
        return category

    def _ms_meets_approval_threshold(self, category):
        """Whether this order is big enough to need approval.

        A threshold of 0 - the default - means every order goes for approval, so
        setting one up is purely additive for anyone already using the module.
        The test is >= : an order landing exactly on the threshold IS approved.
        Compared through the currency so 100,000.00 reads as equal to 100,000
        rather than failing on a float rounding difference.
        """
        self.ensure_one()
        threshold = category.so_approval_threshold
        if threshold <= 0:
            return True
        company = self.company_id or self.env.company
        currency = company.currency_id
        amount = self.amount_total
        if self.currency_id and currency and self.currency_id != currency:
            amount = self.currency_id._convert(
                amount, currency, company, fields.Date.context_today(self))
        return currency.compare_amounts(amount, threshold) >= 0

    def action_confirm(self):
        """Method is used to confirm the order"""
        if not self:
            return super().action_confirm()

        # Decide per order: the governing category depends on the order's company.
        categories = {}
        for order in self:
            if not order.is_approved:
                category = order._ms_approval_category()
                if category:
                    categories[order.id] = category

        orders_requiring_approval = self.filtered(lambda o: o.id in categories)
        orders_not_requiring_approval = self - orders_requiring_approval

        for order in orders_requiring_approval:
            approval = categories[order.id]
            history_vals = []
            for approver in approval.approver_ids:
                history_vals.append({
                    'sale_order_id': order.id,
                    'user_id': approver.user_id.id,
                    'action': 'requested',
                    'note': 'Approval required from this user',
                })
            self.env['sale.approval.history'].sudo().create(history_vals)

            # Created in the ORDER's company: approval.product.line picks up a
            # warehouse from the ambient company, which would otherwise be the
            # confirming user's active company rather than the order's.
            self.env['approval.request'].with_company(order.company_id).create({
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
            # Orders coming back from a completed approval sit in 'approved';
            # the standard confirmation only accepts draft/sent.
            orders_not_requiring_approval.filtered(
                lambda o: o.state == 'approved').write({'state': 'draft'})
            return super(SaleOrder, orders_not_requiring_approval).action_confirm()

        return True
