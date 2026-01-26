from odoo import models
from datetime import datetime, timedelta


class KPIVentas(models.AbstractModel):
    _name = 'chatbot.kpi.ventas'
    _description = 'KPIs de Ventas para Chatbot'

    def get_ventas_mes_actual(self):
        """Total de ventas del mes actual"""
        hoy = datetime.now()
        primer_dia = hoy.replace(day=1, hour=0, minute=0, second=0)

        ventas = self.env['sale.order'].search([
            ('state', 'in', ['sale', 'done']),
            ('date_order', '>=', primer_dia),
        ])
        total = sum(ventas.mapped('amount_total'))
        cantidad = len(ventas)

        return {
            'total': total,
            'cantidad': cantidad,
            'mensaje': f"Este mes llevas ${total:,.2f} en ventas ({cantidad} pedidos confirmados)"
        }

    def get_ventas_mes_anterior(self):
        """Total de ventas del mes anterior"""
        hoy = datetime.now()
        primer_dia_mes_actual = hoy.replace(day=1)
        ultimo_dia_mes_anterior = primer_dia_mes_actual - timedelta(days=1)
        primer_dia_mes_anterior = ultimo_dia_mes_anterior.replace(day=1, hour=0, minute=0, second=0)

        ventas = self.env['sale.order'].search([
            ('state', 'in', ['sale', 'done']),
            ('date_order', '>=', primer_dia_mes_anterior),
            ('date_order', '<=', ultimo_dia_mes_anterior),
        ])
        total = sum(ventas.mapped('amount_total'))
        cantidad = len(ventas)

        return {
            'total': total,
            'cantidad': cantidad,
            'mensaje': f"El mes pasado vendiste ${total:,.2f} ({cantidad} pedidos)"
        }

    def get_pedidos_pendientes(self):
        """Pedidos en estado borrador o presupuesto"""
        pedidos = self.env['sale.order'].search([
            ('state', 'in', ['draft', 'sent']),
        ])
        total = sum(pedidos.mapped('amount_total'))
        cantidad = len(pedidos)

        return {
            'total': total,
            'cantidad': cantidad,
            'mensaje': f"Tienes {cantidad} pedidos pendientes por ${total:,.2f}"
        }

    def get_top_clientes(self, limite=5):
        """Top clientes por monto de ventas"""
        hoy = datetime.now()
        primer_dia = hoy.replace(day=1, hour=0, minute=0, second=0)

        ventas = self.env['sale.order'].search([
            ('state', 'in', ['sale', 'done']),
            ('date_order', '>=', primer_dia),
        ])

        clientes = {}
        for venta in ventas:
            cliente = venta.partner_id.name
            clientes[cliente] = clientes.get(cliente, 0) + venta.amount_total

        top = sorted(clientes.items(), key=lambda x: x[1], reverse=True)[:limite]

        if not top:
            return {'mensaje': "No hay ventas este mes para mostrar top clientes"}

        lineas = [f"{i+1}. {nombre}: ${monto:,.2f}" for i, (nombre, monto) in enumerate(top)]
        return {
            'top': top,
            'mensaje': "Top clientes del mes:\n" + "\n".join(lineas)
        }

    def get_ticket_promedio(self):
        """Ticket promedio de ventas del mes"""
        hoy = datetime.now()
        primer_dia = hoy.replace(day=1, hour=0, minute=0, second=0)

        ventas = self.env['sale.order'].search([
            ('state', 'in', ['sale', 'done']),
            ('date_order', '>=', primer_dia),
        ])

        if not ventas:
            return {'promedio': 0, 'mensaje': "No hay ventas este mes"}

        total = sum(ventas.mapped('amount_total'))
        promedio = total / len(ventas)

        return {
            'promedio': promedio,
            'mensaje': f"El ticket promedio del mes es ${promedio:,.2f}"
        }
