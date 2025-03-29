{
    'name': 'Expense Sharing',
    'version': '1.0',
    'summary': 'Manage and split expenses among group members',
    'author': 'Your Name',
    'depends': ['base', 'mail'],
    'data': [
        'security/ir.model.access.csv',
        'views/expense_group_views.xml',
        'views/menu_items.xml',
        'views/expense_wizard_view.xml',
    ],
    'installable': True,
    'application': True,
}
