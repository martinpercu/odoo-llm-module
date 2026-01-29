from odoo import models
from .helpers import date_range_from_periodo, UMBRAL_REGISTROS


AGRUPAR_MAP = {
    'vendedor': ('user_id', 'Vendedor'),
    'producto': ('product_id', 'Producto'),
    'cliente': ('partner_id', 'Cliente'),
}


class KPIVentas2(models.AbstractModel):
    _name = 'chatbot2.kpi.ventas'
    _description = 'KPI Ventas para Chatbot v2'

    def _build_domain(self, start, end, producto_ids, vendedor_ids, cliente_ids):
        """Construye el domain para ventas."""
        domain = [
            ('state', 'in', ['sale', 'done']),
            ('date_order', '>=', start),
            ('date_order', '<', end),
        ]
        if vendedor_ids:
            domain.append(('user_id', 'in', vendedor_ids))
        if cliente_ids:
            domain.append(('partner_id', 'in', cliente_ids))
        if producto_ids:
            domain.append(('order_line.product_id', 'in', producto_ids))
        return domain

    def get_ventas(self, producto_ids=None, vendedor_ids=None, cliente_ids=None,
                   agrupar_por=None, periodo='mes_actual', limite=20, orden='monto_desc'):
        start, end = date_range_from_periodo(self, periodo)

        if agrupar_por and agrupar_por in AGRUPAR_MAP:
            return self._get_ventas_agrupadas(
                agrupar_por, start, end,
                producto_ids, vendedor_ids, cliente_ids, limite, orden,
            )

        # Sin agrupacion: pedidos individuales
        domain = self._build_domain(start, end, producto_ids, vendedor_ids, cliente_ids)

        # Pre-check de volumen con el mismo domain
        count = self.env['sale.order'].search_count(domain)
        if count > UMBRAL_REGISTROS:
            return {
                'advertencia': True,
                'cantidad': count,
                'periodo': periodo,
                'filtros_actuales': {
                    'producto_ids': producto_ids,
                    'vendedor_ids': vendedor_ids,
                    'cliente_ids': cliente_ids,
                },
                'mensaje': (
                    f"Hay {count} pedidos en el periodo '{periodo}'. "
                    f"Pedile al usuario que acote la busqueda por vendedor, "
                    f"cliente, producto, o cambie el periodo."
                ),
            }

        order_str = 'amount_total desc'
        if orden == 'monto_asc':
            order_str = 'amount_total asc'
        elif orden == 'fecha_desc':
            order_str = 'date_order desc'
        elif orden == 'fecha_asc':
            order_str = 'date_order asc'

        pedidos = self.env['sale.order'].search(domain, limit=limite, order=order_str)

        data = []
        for p in pedidos:
            data.append({
                'id': p.id,
                'nombre': p.name,
                'cliente': p.partner_id.name,
                'cliente_id': p.partner_id.id,
                'vendedor': p.user_id.name if p.user_id else '',
                'vendedor_id': p.user_id.id if p.user_id else None,
                'monto': float(p.amount_total),
                'fecha': str(p.date_order.date()) if p.date_order else '',
            })

        total_monto = sum(d['monto'] for d in data)
        return {
            'ids': [d['id'] for d in data],
            'data': data,
            'total_monto': total_monto,
            'count': len(data),
            'mensaje': f"Se encontraron {len(data)} pedidos por ${total_monto:,.2f}",
        }

    def _get_ventas_agrupadas(self, agrupar_por, start, end,
                               producto_ids, vendedor_ids, cliente_ids, limite, orden):
        field_name, label = AGRUPAR_MAP[agrupar_por]

        domain = [
            ('state', 'in', ['sale', 'done']),
            ('date', '>=', start),
            ('date', '<', end),
        ]
        if producto_ids:
            domain.append(('product_id', 'in', producto_ids))
        if vendedor_ids:
            domain.append(('user_id', 'in', vendedor_ids))
        if cliente_ids:
            domain.append(('partner_id', 'in', cliente_ids))

        order_str = 'price_total desc'
        if 'asc' in orden:
            order_str = 'price_total asc'
        if 'cantidad' in orden:
            order_str = 'product_uom_qty desc'

        results = self.env['sale.report'].read_group(
            domain=domain,
            fields=[field_name, 'price_total', 'product_uom_qty'],
            groupby=[field_name],
            orderby=order_str,
            limit=limite,
        )

        data = []
        for r in results:
            val = r.get(field_name)
            if isinstance(val, tuple):
                entry_id, nombre = val
            else:
                entry_id, nombre = None, str(val)
            data.append({
                'id': entry_id,
                'nombre': nombre,
                'monto': float(r.get('price_total', 0)),
                'cantidad': float(r.get('product_uom_qty', 0)),
            })

        total_monto = sum(d['monto'] for d in data)
        return {
            'agrupado_por': agrupar_por,
            'ids': [d['id'] for d in data if d['id']],
            'data': data,
            'total_monto': total_monto,
            'count': len(data),
            'mensaje': f"Ventas agrupadas por {label}: {len(data)} grupos, total ${total_monto:,.2f}",
        }
