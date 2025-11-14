from odoo import models, fields, api, _
from odoo.exceptions import ValidationError

class LandedCostWizard(models.TransientModel):
    _name = 'landed.cost.wizard'
    _description = 'Landed Cost Report Wizard'

    start_date = fields.Date(string="Start Date")
    end_date = fields.Date(string="End Date")

    # Computed many2many (invisible)
    filtered_purchase_ids = fields.Many2many(
        'purchase.order',
        string="Filtered Purchases",
        compute='_compute_filtered_purchases',
        store=False
    )

    # Purchase field that shows only filtered POs
    purchase = fields.Many2one(
        "purchase.order",
        string="Purchase Order",
        required=True,
        domain="[('id', 'in', filtered_purchase_ids)]"
    )
    @api.onchange('start_date','end_date')
    def checkdate(self):
        if self.start_date and self.end_date:
            if self.end_date < self.start_date:
                return {
                    'warning': {
                        'title': "Invalid Date Range",
                        'message': "End date must be greater than or equal to Start date."
                    }
                }

    @api.depends('start_date', 'end_date')
    def _compute_filtered_purchases(self):
        for rec in self:
            domain = []

            if rec.start_date:
                domain.append(('date_order', '>=', rec.start_date))
            if rec.end_date:
                domain.append(('date_order', '<=', rec.end_date))

            if domain:
                rec.filtered_purchase_ids = self.env['purchase.order'].search(domain)
            else:
                rec.filtered_purchase_ids = self.env['purchase.order'].browse([])

    def action_print_report(self):
        data = {
            'start_date': self.start_date,
            'end_date': self.end_date,
            'purchase_order_id': self.purchase.id,
        }
        return self.env.ref('landed_cost_report.action_landed_cost_report').report_action(self, data=data)

    


class LandedCostReport(models.AbstractModel):
    _name = 'report.landed_cost_report.landed_cost_report_template'
    _description = 'Landed Cost Report'

    def _get_report_values(self, docids, data=None):
        purchase_order = self.env['purchase.order'].browse(data.get('purchase_order_id'))

        return {
            'start_date': data.get('start_date'),
            'end_date': data.get('end_date'),
            'purchase_order': purchase_order,   
        }



