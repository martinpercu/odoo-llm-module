import os
import json
import logging
import openai
from odoo import models, fields, api

_logger = logging.getLogger(__name__)

openai.api_key = os.environ.get('OPENAI_API_KEY')

MAX_ITERACIONES = 10


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


# ---------------------------------------------------------------------------
# Definicion de funciones disponibles para OpenAI
# ---------------------------------------------------------------------------

FUNCIONES_DISPONIBLES = [
    {
        "name": "contar_registros",
        "description": (
            "Cuenta la cantidad de registros que cumplen ciertos filtros "
            "ANTES de consultarlos. Usar siempre antes de get_productos, "
            "get_ventas o get_facturas cuando no se sabe cuantos registros hay, "
            "para decidir si aplicar filtros adicionales o pedir al usuario "
            "que acote la consulta. Modelos disponibles: 'producto', 'venta', 'factura'."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "modelo": {
                    "type": "string",
                    "enum": ["producto", "venta", "factura"],
                    "description": "Tipo de registro a contar",
                },
                "filtros": {
                    "type": "object",
                    "description": (
                        "Filtros opcionales segun el modelo. "
                        "Para producto: {nombre, precio_min, precio_max}. "
                        "Para venta: {producto_ids, vendedor_ids, cliente_ids, periodo, estado}. "
                        "Para factura: {estado, cliente_ids, dias_vencimiento}."
                    ),
                    "properties": {
                        "nombre": {"type": "string"},
                        "precio_min": {"type": "number"},
                        "precio_max": {"type": "number"},
                        "producto_ids": {"type": "array", "items": {"type": "integer"}},
                        "vendedor_ids": {"type": "array", "items": {"type": "integer"}},
                        "cliente_ids": {"type": "array", "items": {"type": "integer"}},
                        "periodo": {
                            "type": "string",
                            "enum": ["mes_actual", "mes_anterior", "trimestre", "anio"],
                        },
                        "estado": {
                            "type": "string",
                            "enum": ["borrador", "confirmado", "pagado", "vencido", "pendiente", "todos"],
                        },
                        "dias_vencimiento": {"type": "integer"},
                    },
                },
            },
            "required": ["modelo"],
        },
    },
    {
        "name": "get_productos",
        "description": (
            "Obtiene lista de productos con id, nombre, precio y stock. "
            "Sirve para buscar productos, ver precios, obtener IDs de "
            "productos para usar en get_ventas. Soporta orden y filtros."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "orden": {
                    "type": "string",
                    "enum": ["precio_asc", "precio_desc", "nombre_asc", "nombre_desc", "stock_asc", "stock_desc"],
                    "description": "Orden de resultados (default: nombre_asc)",
                },
                "limite": {
                    "type": "integer",
                    "description": "Cantidad maxima de productos (default 10)",
                },
                "filtros": {
                    "type": "object",
                    "description": "Filtros opcionales",
                    "properties": {
                        "nombre": {
                            "type": "string",
                            "description": "Buscar por nombre (parcial, case insensitive)",
                        },
                        "precio_min": {"type": "number"},
                        "precio_max": {"type": "number"},
                        "categoria": {
                            "type": "string",
                            "description": "Nombre de categoria de producto",
                        },
                        "ids": {
                            "type": "array",
                            "items": {"type": "integer"},
                            "description": "IDs especificos de productos",
                        },
                    },
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_ventas",
        "description": (
            "Obtiene datos de ventas (pedidos confirmados/realizados). "
            "Puede filtrar por productos, vendedores, clientes, periodo. "
            "Puede agrupar por vendedor, producto, cliente. "
            "Retorna IDs y datos legibles. Ideal para rankings, totales y cruces."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "producto_ids": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "Filtrar por IDs de productos (de get_productos)",
                },
                "vendedor_ids": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "Filtrar por IDs de vendedores",
                },
                "cliente_ids": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "Filtrar por IDs de clientes",
                },
                "agrupar_por": {
                    "type": "string",
                    "enum": ["vendedor", "producto", "cliente"],
                    "description": "Agrupar resultados (default: sin agrupar)",
                },
                "periodo": {
                    "type": "string",
                    "enum": ["mes_actual", "mes_anterior", "trimestre", "anio"],
                    "description": "Periodo a consultar (default: mes_actual)",
                },
                "limite": {
                    "type": "integer",
                    "description": "Cantidad maxima de resultados (default 20)",
                },
                "orden": {
                    "type": "string",
                    "enum": ["monto_desc", "monto_asc", "fecha_desc", "fecha_asc", "cantidad_desc"],
                    "description": "Orden de resultados (default: monto_desc)",
                },
            },
            "required": [],
        },
    },
    {
        "name": "get_facturas",
        "description": (
            "Obtiene datos de facturas (cuentas por cobrar y pagar). "
            "Para ver deudas vencidas, cobros proximos, estados de facturacion. "
            "Filtra por estado, vencimiento, tipo (cliente/proveedor), cliente."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "tipo": {
                    "type": "string",
                    "enum": ["cliente", "proveedor"],
                    "description": "Tipo de factura: cliente (out_invoice) o proveedor (in_invoice). Default: cliente",
                },
                "estado": {
                    "type": "string",
                    "enum": ["pendiente", "vencido", "pagado", "todos"],
                    "description": "Estado de pago. Default: pendiente",
                },
                "dias_vencimiento": {
                    "type": "integer",
                    "description": "Facturas que vencen en los proximos N dias (solo para estado pendiente)",
                },
                "cliente_ids": {
                    "type": "array",
                    "items": {"type": "integer"},
                    "description": "Filtrar por IDs de clientes/proveedores",
                },
                "limite": {
                    "type": "integer",
                    "description": "Cantidad maxima de resultados (default 20)",
                },
            },
            "required": [],
        },
    },
]

SYSTEM_PROMPT = """Eres un asistente de Odoo ERP especializado en datos de negocio.
Tu trabajo es consultar datos de la empresa usando las funciones disponibles.

REGLAS CRITICAS:
1. SIEMPRE usa funciones para obtener datos. NUNCA inventes datos.
2. Para consultas complejas, ENCADENA funciones: usa el resultado de una como entrada de la siguiente.
   Ejemplo: primero get_productos para obtener IDs, luego get_ventas con esos producto_ids.
3. ANTES de consultar datos que podrian ser muchos registros, usa contar_registros para verificar el volumen.
   Si hay mas de 50 registros, pedi al usuario que acote la consulta con filtros.
4. Responde en espanol, conciso y directo.
5. Usa valores por defecto si el usuario no especifica.
6. Si la pregunta no se relaciona con ninguna funcion, indica que consultas podes hacer.
7. Si necesitas aclarar algo de la pregunta del usuario, preguntale directamente.

Funciones disponibles cubren:
- Productos: buscar productos, ver precios, stock, categorias
- Ventas: totales, rankings por vendedor/producto/cliente, periodos
- Facturacion: cuentas por cobrar/pagar, vencimientos, estados

FLUJO RECOMENDADO para consultas complejas:
1. contar_registros -> verificar volumen
2. get_productos/get_ventas/get_facturas -> obtener datos con IDs
3. Encadenar si necesitas cruzar datos (ej: productos -> ventas de esos productos)
"""


# ---------------------------------------------------------------------------
# Modelo principal: Sesion de Chat
# ---------------------------------------------------------------------------

class OdooChatbot2(models.Model):
    _name = 'chatbot.ia2'
    _description = 'Chatbot IA v2 - Sesion de Chat'
    _order = 'create_date desc'

    name = fields.Char(
        string='Sesion',
        default=lambda self: fields.Datetime.now().strftime('%Y-%m-%d %H:%M'),
        readonly=True,
    )
    message_ids = fields.One2many(
        'chatbot.ia2.message', 'session_id',
        string='Mensajes',
    )
    input_text = fields.Char(string='Tu mensaje')
    chat_html = fields.Html(
        string='Chat',
        compute='_compute_chat_html',
        sanitize=False,
    )

    @api.depends('message_ids', 'message_ids.content', 'message_ids.role', 'message_ids.visible')
    def _compute_chat_html(self):
        for record in self:
            html_parts = []
            for msg in record.message_ids.sorted('sequence'):
                if not msg.visible:
                    continue
                content = (msg.content or '').replace('<', '&lt;').replace('>', '&gt;').replace('\n', '<br/>')
                if msg.role == 'user':
                    html_parts.append(
                        '<div style="text-align:right; margin:8px 0;">'
                        '<span style="background:#d1ecf1; padding:10px 16px; '
                        'border-radius:14px 14px 4px 14px; display:inline-block; '
                        'max-width:80%%; text-align:left; font-size:13px;">'
                        '<b>Vos:</b><br/>%s</span></div>' % content
                    )
                elif msg.role == 'assistant':
                    html_parts.append(
                        '<div style="text-align:left; margin:8px 0;">'
                        '<span style="background:#d4edda; padding:10px 16px; '
                        'border-radius:14px 14px 14px 4px; display:inline-block; '
                        'max-width:80%%; font-size:13px;">'
                        '<b>Asistente:</b><br/>%s</span></div>' % content
                    )
            record.chat_html = (
                ''.join(html_parts) if html_parts
                else '<p style="color:#888; text-align:center;">Hace una pregunta para empezar...</p>'
            )

    # ------------------------------------------------------------------
    # Acciones de UI
    # ------------------------------------------------------------------

    def accion_enviar(self):
        self.ensure_one()
        if not self.input_text:
            return
        user_text = self.input_text
        self.input_text = False

        # Inyectar system prompt si es el primer mensaje
        if not self.message_ids.filtered(lambda m: m.role == 'system'):
            self._crear_mensaje('system', SYSTEM_PROMPT, visible=False)

        # Agregar mensaje del usuario
        self._crear_mensaje('user', user_text)

        # Ejecutar loop de OpenAI
        self._ejecutar_loop_openai()

    def accion_nueva_sesion(self):
        nueva = self.create({})
        return {
            'type': 'ir.actions.act_window',
            'res_model': 'chatbot.ia2',
            'view_mode': 'form',
            'res_id': nueva.id,
            'target': 'current',
        }

    # ------------------------------------------------------------------
    # Loop OpenAI con funciones encadenadas
    # ------------------------------------------------------------------

    def _ejecutar_loop_openai(self):
        """Loop: enviar historial -> si function_call ejecutar y repetir -> si texto, fin."""
        for i in range(MAX_ITERACIONES):
            mensajes_api = self._construir_historial_api()

            try:
                response = openai.ChatCompletion.create(
                    model="gpt-4o-mini",
                    messages=mensajes_api,
                    functions=FUNCIONES_DISPONIBLES,
                    function_call="auto",
                    temperature=0.3,
                )
            except Exception as e:
                _logger.error("Error OpenAI en iteracion %d: %s", i, str(e))
                self._crear_mensaje('assistant', f"Error al consultar IA: {str(e)}")
                return

            mensaje = response.choices[0].message

            if mensaje.get("function_call"):
                nombre = mensaje["function_call"]["name"]
                args_str = mensaje["function_call"].get("arguments", "{}")

                try:
                    argumentos = json.loads(args_str)
                except json.JSONDecodeError:
                    argumentos = {}

                # Guardar la decision del asistente (oculto en el chat)
                self._crear_mensaje(
                    'assistant',
                    json.dumps({
                        "function_call": {
                            "name": nombre,
                            "arguments": args_str,
                        }
                    }, ensure_ascii=False),
                    visible=False,
                    function_name=nombre,
                )

                # Ejecutar la funcion
                resultado = self._ejecutar_funcion(nombre, argumentos)

                # Guardar resultado de la funcion (oculto en el chat)
                self._crear_mensaje(
                    'function',
                    json.dumps(resultado, ensure_ascii=False, cls=OdooJSONEncoder),
                    visible=False,
                    function_name=nombre,
                )
                _logger.info("Iteracion %d: funcion '%s' ejecutada", i, nombre)
                # Continuar loop para que GPT procese el resultado
            else:
                # GPT respondio con texto
                contenido = mensaje.get("content", "No pude procesar tu consulta.")
                self._crear_mensaje('assistant', contenido)
                return

        # Limite de seguridad alcanzado
        self._crear_mensaje(
            'assistant',
            "Se alcanzo el limite de operaciones. Por favor, reformula tu pregunta.",
        )

    # ------------------------------------------------------------------
    # Construccion del historial para la API
    # ------------------------------------------------------------------

    def _construir_historial_api(self):
        """Convierte los mensajes almacenados al formato que espera OpenAI."""
        mensajes = []
        for msg in self.message_ids.sorted('sequence'):
            if msg.role == 'function':
                mensajes.append({
                    "role": "function",
                    "name": msg.function_name,
                    "content": msg.content or "",
                })
            elif msg.role == 'assistant' and msg.function_name:
                # Mensaje del asistente que contiene un function_call
                try:
                    data = json.loads(msg.content)
                    mensajes.append({
                        "role": "assistant",
                        "content": None,
                        "function_call": {
                            "name": data["function_call"]["name"],
                            "arguments": data["function_call"]["arguments"],
                        },
                    })
                except (json.JSONDecodeError, KeyError):
                    mensajes.append({
                        "role": "assistant",
                        "content": msg.content or "",
                    })
            else:
                mensajes.append({
                    "role": msg.role,
                    "content": msg.content or "",
                })
        return mensajes

    # ------------------------------------------------------------------
    # Dispatcher de funciones
    # ------------------------------------------------------------------

    def _ejecutar_funcion(self, nombre, argumentos):
        """Rutea las llamadas de funciones a los handlers KPI correspondientes."""
        try:
            if nombre == 'contar_registros':
                return self.env['chatbot2.kpi.contador'].contar_registros(
                    argumentos.get('modelo'),
                    argumentos.get('filtros', {}),
                )
            elif nombre == 'get_productos':
                return self.env['chatbot2.kpi.productos'].get_productos(
                    orden=argumentos.get('orden', 'nombre_asc'),
                    limite=argumentos.get('limite', 10),
                    filtros=argumentos.get('filtros', {}),
                )
            elif nombre == 'get_ventas':
                return self.env['chatbot2.kpi.ventas'].get_ventas(
                    producto_ids=argumentos.get('producto_ids'),
                    vendedor_ids=argumentos.get('vendedor_ids'),
                    cliente_ids=argumentos.get('cliente_ids'),
                    agrupar_por=argumentos.get('agrupar_por'),
                    periodo=argumentos.get('periodo', 'mes_actual'),
                    limite=argumentos.get('limite', 20),
                    orden=argumentos.get('orden', 'monto_desc'),
                )
            elif nombre == 'get_facturas':
                return self.env['chatbot2.kpi.facturacion'].get_facturas(
                    tipo=argumentos.get('tipo', 'cliente'),
                    estado=argumentos.get('estado', 'pendiente'),
                    dias_vencimiento=argumentos.get('dias_vencimiento'),
                    cliente_ids=argumentos.get('cliente_ids'),
                    limite=argumentos.get('limite', 20),
                )
            return {'error': True, 'mensaje': f"Funcion '{nombre}' no disponible"}
        except Exception as e:
            _logger.error("Error ejecutando funcion '%s': %s", nombre, str(e))
            return {'error': True, 'mensaje': f"Error al ejecutar '{nombre}': {str(e)}"}

    # ------------------------------------------------------------------
    # Helper para crear mensajes
    # ------------------------------------------------------------------

    def _crear_mensaje(self, role, content, visible=None, function_name=False):
        """Crea un nuevo mensaje en la sesion."""
        if visible is None:
            visible = role in ('user', 'assistant') and not function_name
        max_seq = max(self.message_ids.mapped('sequence') or [0])
        self.env['chatbot.ia2.message'].create({
            'session_id': self.id,
            'sequence': max_seq + 1,
            'role': role,
            'content': content,
            'function_name': function_name,
            'visible': visible,
        })
