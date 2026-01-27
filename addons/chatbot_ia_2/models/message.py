from odoo import models, fields


class ChatbotMessage(models.Model):
    _name = 'chatbot.ia2.message'
    _description = 'Mensaje de Chat'
    _order = 'sequence asc, id asc'

    session_id = fields.Many2one(
        'chatbot.ia2', string='Sesion',
        required=True, ondelete='cascade',
    )
    sequence = fields.Integer(string='Orden', default=10)
    role = fields.Selection([
        ('user', 'Usuario'),
        ('assistant', 'Asistente'),
        ('system', 'Sistema'),
        ('function', 'Funcion'),
    ], string='Rol', required=True)
    content = fields.Text(string='Contenido')
    function_name = fields.Char(string='Nombre Funcion')
    visible = fields.Boolean(string='Visible', default=True)
