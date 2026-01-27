from odoo import models
from .helpers import today, date_range_from_periodo


class KPIContador(models.AbstractModel):
    _name = 'chatbot2.kpi.contador'
    _description = 'Contador de registros para pre-check de volumen'

    def contar_registros(self, modelo, filtros=None):
        filtros = filtros or {}

        if modelo == 'producto':
            domain = [('sale_ok', '=', True)]
            if filtros.get('nombre'):
                domain.append(('name', 'ilike', filtros['nombre']))
            if filtros.get('precio_min') is not None:
                domain.append(('list_price', '>=', filtros['precio_min']))
            if filtros.get('precio_max') is not None:
                domain.append(('list_price', '<=', filtros['precio_max']))
            count = self.env['product.product'].search_count(domain)

        elif modelo == 'venta':
            domain = [('state', 'in', ['sale', 'done'])]
            periodo = filtros.get('periodo', 'mes_actual')
            start, end = date_range_from_periodo(self, periodo)
            domain += [('date_order', '>=', start), ('date_order', '<', end)]
            if filtros.get('producto_ids'):
                domain.append(('order_line.product_id', 'in', filtros['producto_ids']))
            if filtros.get('vendedor_ids'):
                domain.append(('user_id', 'in', filtros['vendedor_ids']))
            if filtros.get('cliente_ids'):
                domain.append(('partner_id', 'in', filtros['cliente_ids']))
            count = self.env['sale.order'].search_count(domain)

        elif modelo == 'factura':
            domain = [('state', '=', 'posted')]
            estado = filtros.get('estado')
            if estado == 'vencido':
                domain += [
                    ('payment_state', 'in', ['not_paid', 'partial']),
                    ('invoice_date_due', '<', today(self)),
                ]
            elif estado in ('pendiente', None):
                domain.append(('payment_state', 'in', ['not_paid', 'partial']))
            elif estado == 'pagado':
                domain.append(('payment_state', '=', 'paid'))
            if filtros.get('cliente_ids'):
                domain.append(('partner_id', 'in', filtros['cliente_ids']))
            if filtros.get('dias_vencimiento'):
                from dateutil.relativedelta import relativedelta
                hoy = today(self)
                fecha_limite = hoy + relativedelta(days=filtros['dias_vencimiento'])
                domain += [
                    ('invoice_date_due', '>=', hoy),
                    ('invoice_date_due', '<=', fecha_limite),
                ]
            count = self.env['account.move'].search_count(domain)

        else:
            return {'error': True, 'mensaje': f"Modelo '{modelo}' no soportado. Usa: producto, venta, factura."}

        return {
            'modelo': modelo,
            'cantidad': count,
            'filtros_aplicados': filtros,
            'mensaje': f"Hay {count} registros de '{modelo}' con los filtros aplicados.",
        }
