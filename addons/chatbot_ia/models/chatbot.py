import os
import json
import openai
from odoo import models, fields

# Configurar API key desde variable de entorno
openai.api_key = os.environ.get('OPENAI_API_KEY')

# Definición de funciones disponibles para el LLM
FUNCIONES_DISPONIBLES = [
    {
        "name": "get_ventas_mes_actual",
        "description": "Obtiene el total de ventas del mes actual, cantidad de pedidos y monto total",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "get_ventas_mes_anterior",
        "description": "Obtiene el total de ventas del mes anterior",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "get_pedidos_pendientes",
        "description": "Obtiene los pedidos pendientes (borradores y presupuestos sin confirmar)",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "get_top_clientes",
        "description": "Obtiene el ranking de los mejores clientes por monto de ventas del mes",
        "parameters": {
            "type": "object",
            "properties": {
                "limite": {
                    "type": "integer",
                    "description": "Cantidad de clientes a mostrar (default 5)"
                }
            },
            "required": []
        }
    },
    {
        "name": "get_ticket_promedio",
        "description": "Obtiene el ticket promedio de ventas del mes actual",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "get_cantidad_empleados",
        "description": "Obtiene la cantidad de empleados registrados en el sistema",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
]

SYSTEM_PROMPT = """Eres un asistente de Odoo ERP especializado en KPIs de negocio.
Tu trabajo es ayudar a los usuarios a consultar información sobre ventas, compras, facturación e inventario.

Responde siempre en español de forma concisa y amigable.
Si no puedes responder algo, indica qué tipo de consultas sí puedes hacer.

Módulos disponibles actualmente:
- Ventas: total del mes, mes anterior, pedidos pendientes, top clientes, ticket promedio
- RRHH: cantidad de empleados
"""


class OdooChatbot(models.Model):
    _name = 'chatbot.ia'
    _description = 'Chatbot de Inteligencia Artificial'

    pregunta = fields.Char(string='Tu pregunta')
    respuesta = fields.Text(string='Respuesta', readonly=True)

    def _ejecutar_funcion(self, nombre_funcion, argumentos):
        """Ejecuta la función solicitada por el LLM"""
        kpi_ventas = self.env['chatbot.kpi.ventas']

        if nombre_funcion == 'get_ventas_mes_actual':
            return kpi_ventas.get_ventas_mes_actual()
        elif nombre_funcion == 'get_ventas_mes_anterior':
            return kpi_ventas.get_ventas_mes_anterior()
        elif nombre_funcion == 'get_pedidos_pendientes':
            return kpi_ventas.get_pedidos_pendientes()
        elif nombre_funcion == 'get_top_clientes':
            limite = argumentos.get('limite', 5)
            return kpi_ventas.get_top_clientes(limite)
        elif nombre_funcion == 'get_ticket_promedio':
            return kpi_ventas.get_ticket_promedio()
        elif nombre_funcion == 'get_cantidad_empleados':
            cantidad = self.env['hr.employee'].search_count([])
            return {'mensaje': f"Hay {cantidad} empleados registrados en el sistema"}

        return {'mensaje': "Función no disponible"}

    def accion_consultar(self):
        for record in self:
            if not record.pregunta:
                record.respuesta = "Por favor, escribe una pregunta"
                continue

            try:
                # Primera llamada: el LLM decide qué función usar
                response = openai.ChatCompletion.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": record.pregunta}
                    ],
                    functions=FUNCIONES_DISPONIBLES,
                    function_call="auto",
                    temperature=0.3,
                )

                mensaje = response.choices[0].message

                # Si el LLM quiere llamar una función
                if mensaje.get("function_call"):
                    nombre_funcion = mensaje["function_call"]["name"]
                    argumentos = json.loads(mensaje["function_call"].get("arguments", "{}"))

                    # Ejecutar la función
                    resultado = record._ejecutar_funcion(nombre_funcion, argumentos)

                    # Segunda llamada: el LLM formatea la respuesta
                    response2 = openai.ChatCompletion.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": record.pregunta},
                            mensaje,
                            {
                                "role": "function",
                                "name": nombre_funcion,
                                "content": json.dumps(resultado, ensure_ascii=False)
                            }
                        ],
                        temperature=0.3,
                    )
                    record.respuesta = response2.choices[0].message["content"]
                else:
                    # Respuesta directa sin función
                    record.respuesta = mensaje.get("content", "No pude procesar tu consulta")

            except Exception as e:
                record.respuesta = f"Error al procesar: {str(e)}"
