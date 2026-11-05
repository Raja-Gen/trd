{
    'name': "Purchase Approval Connector",
    'version': "19.0.1.0.0",
    'category': 'Purchase',
    'summary': """Setting up a system where all Purchase orders must be approved at
     a higher level before they can be processed or fulfilled.""",
    'description': """This process ensures that orders are reviewed and 
    approved by designated users before they are confirmed and processed.""",
    'author': "Micro Solutions Kuwait",
    'company': "Micro Solutions Kuwait",
    'depends': ['purchase', 'approvals'],
    'data': [
        'security/ir.model.access.csv',
        'data/approval_connector.xml',
        'views/approval_category.xml',
        'views/purchase_order_view.xml',
        'views/approval_request.xml',
        ],
    'installable': True,
    'auto_install': False,
    'application': False,
}
