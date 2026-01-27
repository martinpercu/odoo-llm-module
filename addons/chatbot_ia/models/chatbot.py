import os
import json
import openai
from odoo import models, fields

openai.api_key = os.environ.get('OPENAI_API_KEY')


class OdooJSONEncoder(json.JSONEncoder):
    """Encoder que convierte tipos lazy de Odoo a tipos nativos de Python"""
    def default(self, obj):
        try:
            return float(obj)
        except (TypeError, ValueError):
            pass
        try:
            return str(obj)
        except (TypeError, ValueError):
            pass
        return super().default(obj)

FUNCIONES_DISPONIBLES = [
    # === VENTAS ===
    {
        "name": "get_ventas_mes_actual",
        "description": "Obtiene el total de ventas del mes actual: cuánto se vendió, cuántos pedidos hubo, monto total y comparación con el mes anterior. Usar cuando pregunten: cuánto vendimos, ventas del mes, cómo van las ventas, resumen de ventas.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "get_top_productos",
        "description": "Ranking de productos más vendidos del mes por ingreso. Usar cuando pregunten: qué productos se venden más, mejores productos, top productos, productos estrella.",
        "parameters": {
            "type": "object",
            "properties": {
                "limite": {
                    "type": "integer",
                    "description": "Cantidad de productos a mostrar (default 5)"
                }
            },
            "required": []
        }
    },
    {
        "name": "get_pedidos_pendientes",
        "description": "Pedidos de venta sin confirmar (borradores/presupuestos). Usar cuando pregunten: pedidos pendientes, presupuestos sin confirmar, qué falta cerrar.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "get_top_clientes",
        "description": "Ranking de mejores clientes por monto de compra del mes. Usar cuando pregunten: mejores clientes, quién compra más, top clientes, clientes principales.",
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
        "description": "Monto promedio por pedido de venta del mes. Usar cuando pregunten: ticket promedio, promedio por venta, cuánto es la venta promedio.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    # === COMPRAS ===
    {
        "name": "get_compras_mes_actual",
        "description": "Total de compras del mes actual: cuánto se compró, cantidad de órdenes, y comparación con el mes anterior. Usar cuando pregunten: cuánto compramos, compras del mes, gastos en compras, resumen de compras.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "get_top_proveedores",
        "description": "Ranking de proveedores con mayor volumen de compras del mes. Usar cuando pregunten: top proveedores, a quién le compramos más, proveedores principales.",
        "parameters": {
            "type": "object",
            "properties": {
                "limite": {
                    "type": "integer",
                    "description": "Cantidad de proveedores a mostrar (default 5)"
                }
            },
            "required": []
        }
    },
    # === FACTURACIÓN ===
    {
        "name": "get_cuentas_por_cobrar_vencidas",
        "description": "Facturas vencidas que los clientes nos deben. Usar cuando pregunten: cuánto nos deben, deuda de clientes, cuentas por cobrar, CxC, morosidad, facturas vencidas de clientes, plata que nos deben.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "get_cuentas_por_pagar_vencidas",
        "description": "Facturas vencidas que nosotros debemos a proveedores. Usar cuando pregunten: cuánto debemos, deuda con proveedores, cuentas por pagar, CxP, facturas vencidas de proveedores, qué tenemos que pagar, cuánto debemos a proveedores.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
    {
        "name": "get_por_cobrar_proximos_dias",
        "description": "Monto que vamos a cobrar de clientes en los próximos días según vencimiento. Usar cuando pregunten: qué vamos a cobrar, ingresos próximos, cobros pendientes, cuánto entra pronto.",
        "parameters": {
            "type": "object",
            "properties": {
                "dias": {
                    "type": "integer",
                    "description": "Cantidad de días a futuro (default 10)"
                }
            },
            "required": []
        }
    },
    # === RRHH ===
    {
        "name": "get_cantidad_empleados",
        "description": "Cantidad de empleados en el sistema. Usar cuando pregunten: cuántos empleados hay, cantidad de personal, headcount, dotación.",
        "parameters": {"type": "object", "properties": {}, "required": []}
    },
]

SYSTEM_PROMPT = """Eres un asistente de Odoo ERP especializado en KPIs de negocio.
Tu trabajo es consultar datos de la empresa cuando el usuario lo pida.

REGLAS CRÍTICAS:
1. SIEMPRE ejecuta una función cuando el usuario pida cualquier dato. NUNCA respondas sin ejecutar una función primero.
2. NUNCA pidas confirmación, NUNCA ofrezcas opciones, NUNCA preguntes antes de ejecutar. Simplemente ejecuta.
3. Si la pregunta puede resolverse con alguna función disponible, ÚSALA de inmediato.
4. Usa valores por defecto si el usuario no especifica (ej: top 5, 10 días).
5. Responde en español, conciso y directo.
6. Solo si la pregunta NO se relaciona con ninguna función disponible, indica qué consultas puedes hacer.

Funciones disponibles cubren:
- Ventas: total mensual, top productos, top clientes, pedidos pendientes, ticket promedio
- Compras: total mensual, top proveedores
- Facturación: deuda de clientes (CxC), deuda con proveedores (CxP), cobros próximos
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
        kpi_compras = self.env['chatbot.kpi.compras']
        kpi_facturacion = self.env['chatbot.kpi.facturacion']

        # Ventas
        if nombre_funcion == 'get_ventas_mes_actual':
            return kpi_ventas.get_ventas_mes_actual()
        elif nombre_funcion == 'get_top_productos':
            return kpi_ventas.get_top_productos(argumentos.get('limite', 5))
        elif nombre_funcion == 'get_pedidos_pendientes':
            return kpi_ventas.get_pedidos_pendientes()
        elif nombre_funcion == 'get_top_clientes':
            return kpi_ventas.get_top_clientes(argumentos.get('limite', 5))
        elif nombre_funcion == 'get_ticket_promedio':
            return kpi_ventas.get_ticket_promedio()

        # Compras
        elif nombre_funcion == 'get_compras_mes_actual':
            return kpi_compras.get_compras_mes_actual()
        elif nombre_funcion == 'get_top_proveedores':
            return kpi_compras.get_top_proveedores(argumentos.get('limite', 5))

        # Facturación
        elif nombre_funcion == 'get_cuentas_por_cobrar_vencidas':
            return kpi_facturacion.get_cuentas_por_cobrar_vencidas()
        elif nombre_funcion == 'get_cuentas_por_pagar_vencidas':
            return kpi_facturacion.get_cuentas_por_pagar_vencidas()
        elif nombre_funcion == 'get_por_cobrar_proximos_dias':
            return kpi_facturacion.get_por_cobrar_proximos_dias(argumentos.get('dias', 10))

        # RRHH
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

                if mensaje.get("function_call"):
                    nombre_funcion = mensaje["function_call"]["name"]
                    argumentos = json.loads(mensaje["function_call"].get("arguments", "{}"))

                    resultado = record._ejecutar_funcion(nombre_funcion, argumentos)

                    response2 = openai.ChatCompletion.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": SYSTEM_PROMPT},
                            {"role": "user", "content": record.pregunta},
                            mensaje,
                            {
                                "role": "function",
                                "name": nombre_funcion,
                                "content": json.dumps(resultado, ensure_ascii=False, cls=OdooJSONEncoder)
                            }
                        ],
                        temperature=0.3,
                    )
                    record.respuesta = response2.choices[0].message["content"]
                else:
                    record.respuesta = mensaje.get("content", "No pude procesar tu consulta")

            except Exception as e:
                record.respuesta = f"Error al procesar: {str(e)}"
