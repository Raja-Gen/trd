from odoo import fields, models


class ApprovalCategory(models.Model):
    _inherit = 'approval.category'

    po_approval_threshold = fields.Float(
        string="PO Final-Approval Threshold",
        digits=(16, 2),
        help="When a Purchase Order total exceeds this amount, the order "
             "requires an extra final approval from the configured approver "
             "after the normal approval chain completes. Currency-agnostic: the "
             "total is compared as a plain number, whatever currency the order "
             "is in. Leave at 0 to disable.",
    )
    po_final_approver_id = fields.Many2one(
        'res.users',
        string="PO Final Approver",
        help="User appended as the LAST approver when a Purchase Order total "
             "exceeds the threshold above. The normal approval chain runs "
             "first; this user approves last.",
    )
