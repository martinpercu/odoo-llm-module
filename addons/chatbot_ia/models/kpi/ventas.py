from odoo import models
from .helpers import month_range, prev_month_range, variacion_porcentual


class KPIVentas(models.AbstractModel):
    _name = 'chatbot.kpi.ventas'
    _description = 'KPIs de Ventas para Chatbot'

    def get_ventas_mes_actual(self):
        """KPI 1: Total ventas del mes actual + variación vs mes anterior"""
        start_m, end_m = month_range(self)
        start_pm, end_pm = prev_month_range(self)

        ventas_actual = self.env['sale.order'].search([
            ('state', 'in', ['sale', 'done']),
            ('date_order', '>=', start_m),
            ('date_order', '<', end_m),
        ])
        total_actual = sum(ventas_actual.mapped('amount_total'))
        cantidad_actual = len(ventas_actual)

        ventas_anterior = self.env['sale.order'].search([
            ('state', 'in', ['sale', 'done']),
            ('date_order', '>=', start_pm),
            ('date_order', '<', end_pm),
        ])
        total_anterior = sum(ventas_anterior.mapped('amount_total'))
        cantidad_anterior = len(ventas_anterior)

        variacion = variacion_porcentual(total_actual, total_anterior)

        return {
            'total_actual': total_actual,
            'cantidad_actual': cantidad_actual,
            'total_anterior': total_anterior,
            'cantidad_anterior': cantidad_anterior,
            'variacion_porcentual': variacion,
            'mensaje': (
                f"Ventas del mes actual: ${total_actual:,.2f} ({cantidad_actual} pedidos). "
                f"Mes anterior: ${total_anterior:,.2f} ({cantidad_anterior} pedidos). "
                f"Variación: {variacion:+.1f}%"
            )
        }

    def get_top_productos(self, limite=5):
        """KPI 2: Top productos por ingreso del mes (usa sale.report)"""
        start_m, end_m = month_range(self)

        data = self.env['sale.report'].read_group(
            domain=[
                ('state', 'in', ['sale', 'done']),
                ('date', '>=', start_m),
                ('date', '<', end_m),
                ('product_id', '!=', False),
            ],
            fields=['product_id', 'price_total'],
            groupby=['product_id'],
            orderby='price_total desc',
            limit=limite,
        )

        if not data:
            return {'mensaje': "No hay ventas este mes para mostrar top productos"}

        lineas = []
        for i, item in enumerate(data):
            nombre = item['product_id'][1]
            monto = float(item['price_total'])
            lineas.append(f"{i+1}. {nombre}: ${monto:,.2f}")

        return {
            'top': [{'producto': d['product_id'][1], 'monto': float(d['price_total'])} for d in data],
            'mensaje': "Top productos del mes por ingreso:\n" + "\n".join(lineas)
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
        """Top clientes por monto de ventas del mes"""
        start_m, end_m = month_range(self)

        ventas = self.env['sale.order'].search([
            ('state', 'in', ['sale', 'done']),
            ('date_order', '>=', start_m),
            ('date_order', '<', end_m),
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
            'top': [{'cliente': n, 'monto': m} for n, m in top],
            'mensaje': "Top clientes del mes:\n" + "\n".join(lineas)
        }

    def get_ticket_promedio(self):
        """Ticket promedio de ventas del mes"""
        start_m, end_m = month_range(self)

        ventas = self.env['sale.order'].search([
            ('state', 'in', ['sale', 'done']),
            ('date_order', '>=', start_m),
            ('date_order', '<', end_m),
        ])

        if not ventas:
            return {'promedio': 0, 'mensaje': "No hay ventas este mes"}

        total = sum(ventas.mapped('amount_total'))
        promedio = total / len(ventas)

        return {
            'promedio': promedio,
            'mensaje': f"El ticket promedio del mes es ${promedio:,.2f}"
        }
