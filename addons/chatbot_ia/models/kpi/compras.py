from odoo import models
from .helpers import month_range, prev_month_range, variacion_porcentual


class KPICompras(models.AbstractModel):
    _name = 'chatbot.kpi.compras'
    _description = 'KPIs de Compras para Chatbot'

    def get_compras_mes_actual(self):
        """KPI 3: Total compras del mes actual + variación vs mes anterior"""
        start_m, end_m = month_range(self)
        start_pm, end_pm = prev_month_range(self)

        compras_actual = self.env['purchase.order'].search([
            ('state', 'in', ['purchase', 'done']),
            ('date_order', '>=', start_m),
            ('date_order', '<', end_m),
        ])
        total_actual = sum(compras_actual.mapped('amount_total'))
        cantidad_actual = len(compras_actual)

        compras_anterior = self.env['purchase.order'].search([
            ('state', 'in', ['purchase', 'done']),
            ('date_order', '>=', start_pm),
            ('date_order', '<', end_pm),
        ])
        total_anterior = sum(compras_anterior.mapped('amount_total'))
        cantidad_anterior = len(compras_anterior)

        variacion = variacion_porcentual(total_actual, total_anterior)

        return {
            'total_actual': total_actual,
            'cantidad_actual': cantidad_actual,
            'total_anterior': total_anterior,
            'cantidad_anterior': cantidad_anterior,
            'variacion_porcentual': variacion,
            'mensaje': (
                f"Compras del mes actual: ${total_actual:,.2f} ({cantidad_actual} órdenes). "
                f"Mes anterior: ${total_anterior:,.2f} ({cantidad_anterior} órdenes). "
                f"Variación: {variacion:+.1f}%"
            )
        }

    def get_top_proveedores(self, limite=5):
        """KPI 4: Top proveedores por volumen de compras del mes"""
        start_m, end_m = month_range(self)

        data = self.env['purchase.report'].read_group(
            domain=[
                ('state', 'in', ['purchase', 'done']),
                ('date_order', '>=', start_m),
                ('date_order', '<', end_m),
                ('partner_id', '!=', False),
            ],
            fields=['partner_id', 'price_total'],
            groupby=['partner_id'],
            orderby='price_total desc',
            limit=limite,
        )

        if not data:
            return {'mensaje': "No hay compras este mes para mostrar top proveedores"}

        lineas = []
        for i, item in enumerate(data):
            nombre = item['partner_id'][1]
            monto = float(item['price_total'])
            lineas.append(f"{i+1}. {nombre}: ${monto:,.2f}")

        return {
            'top': [{'proveedor': d['partner_id'][1], 'monto': float(d['price_total'])} for d in data],
            'mensaje': "Top proveedores del mes por volumen de compras:\n" + "\n".join(lineas)
        }
