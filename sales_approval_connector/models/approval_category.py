# -*- coding: utf-8 -*-
###############################################################################
#
#   Copyright (C) 2024-TODAY Cybrosys Technologies(<https://www.cybrosys.com>)
#   Author: AFRA MP (odoo@cybrosys.com)
#
#   This program is under the terms of the Odoo Proprietary License v1.0 (OPL-1)
#   It is forbidden to publish, distribute, sublicense, or sell copies of the
#   Software or modified copies of the Software.
#
#   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT.
#   IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM,
#   DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
#   OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE
#   USE OR OTHER DEALINGS IN THE SOFTWARE.
#
###############################################################################
from odoo import api, fields, models


class ApprovalCategory(models.Model):
    _inherit = 'approval.category'
    """Class inherited for the category associated with approval category
    also add some additional fields"""

    approval_type = fields.Selection(
        selection_add=[
            ('purchase', "Purchase"),
            ('sale', "Sale"),
            ('invoice', "Invoice"),
            ('expense' , "Expense"),
            ('inventory' , "Inventory") 
        ],
        string="Approval Type",

        ondelete={
            'generic': 'cascade',  
            'purchase': 'cascade',
            'sale': 'cascade',
            'invoice': 'cascade',
            'expense': 'cascade',
            'inventory':'cascade',
        },

        help="Approval type to identify the model",
    )

    so_approval_threshold = fields.Float(
        string="Sale Approval Threshold",
        digits=(16, 2),
        help="Sale orders are sent for approval only when their total reaches "
             "this amount. Deliberately currency-agnostic: the order's total is "
             "compared as a plain number, so 10,000 means 10,000 AED on an AED "
             "order and 10,000 KWD on a KWD one. An order exactly on the "
             "threshold is included. Leave at 0 to send every order for approval.",
    )
