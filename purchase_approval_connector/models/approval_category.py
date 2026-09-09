from odoo import api, fields, models


class ApprovalCategory(models.Model):
    _inherit = 'approval.category'

    company_currency_id = fields.Many2one(
        'res.currency',
        string="Company Currency",
        compute='_compute_company_currency_id',
    )

    po_approval_threshold = fields.Monetary(
        string="PO Final-Approval Threshold",
        currency_field='company_currency_id',
        help="When a Purchase Order total (in company currency) exceeds this "
             "amount, the order requires an extra final approval from the "
             "configured approver after the normal approval chain completes. "
             "Leave at 0 to disable.",
    )
    po_final_approver_id = fields.Many2one(
        'res.users',
        string="PO Final Approver",
        help="User appended as the LAST approver when a Purchase Order total "
             "exceeds the threshold above. The normal approval chain runs "
             "first; this user approves last.",
    )

    @api.depends('company_id')
    def _compute_company_currency_id(self):
        for category in self:
            company = category.company_id or self.env.company
            category.company_currency_id = company.currency_id
