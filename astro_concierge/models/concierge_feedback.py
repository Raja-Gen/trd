from odoo import models, fields

class ConciergeFeedback(models.Model):
    _name = 'concierge.feedback'
    _description = 'Concierge Feedback'
    _rec_name = 'request_id'

    request_id = fields.Many2one('concierge.request', string='Related Request', ondelete='cascade')
    rating = fields.Selection([
        ('1', 'Very Poor'),
        ('2', 'Poor'),
        ('3', 'Average'),
        ('4', 'Good'),
        ('5', 'Excellent')
    ], string='Satisfaction Rating', required=True)
    comment = fields.Text(string='Comment')
    submitted_by = fields.Many2one('res.users', string='Submitted By', default=lambda self: self.env.user)
    submitted_on = fields.Datetime(string='Submitted On', default=fields.Datetime.now)
