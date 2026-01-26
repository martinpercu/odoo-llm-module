{
    'name': 'Chatbot IA Odoo',
    'version': '1.1',
    'summary': 'Consulta KPIs de Odoo con lenguaje natural usando IA',
    'category': 'Tools',
    'author': 'Martin Mendez',
    'depends': ['base', 'hr', 'sale'],
    'data': [
        'security/ir.model.access.csv',
        'views/chatbot_view.xml',
    ],
    'external_dependencies': {
        'python': ['openai'],
    },
    'installable': True,
    'application': True,
}