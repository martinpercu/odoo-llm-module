{
    'name': 'Chatbot IA Odoo 2',
    'version': '2.0',
    'summary': 'Chat multi-turno con IA para consultar KPIs de Odoo',
    'category': 'Tools',
    'author': 'Martin Mendez',
    'depends': ['base', 'sale', 'account', 'product', 'stock'],
    'data': [
        'security/ir.model.access.csv',
        'views/assets.xml',
        'views/chatbot_view.xml',
    ],
    'external_dependencies': {
        'python': ['openai'],
    },
    'installable': True,
    'application': True,
}
