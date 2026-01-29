from odoo import models
from .helpers import UMBRAL_REGISTROS


ORDEN_MAP = {
    'precio_asc': 'list_price asc',
    'precio_desc': 'list_price desc',
    'nombre_asc': 'name asc',
    'nombre_desc': 'name desc',
    'stock_asc': 'qty_available asc',
    'stock_desc': 'qty_available desc',
}


class KPIProductos(models.AbstractModel):
    _name = 'chatbot2.kpi.productos'
    _description = 'KPI Productos para Chatbot v2'

    def _build_domain(self, filtros):
        """Construye el domain para productos."""
        domain = [('sale_ok', '=', True)]
        if filtros.get('nombre'):
            domain.append(('name', 'ilike', filtros['nombre']))
        if filtros.get('precio_min') is not None:
            domain.append(('list_price', '>=', filtros['precio_min']))
        if filtros.get('precio_max') is not None:
            domain.append(('list_price', '<=', filtros['precio_max']))
        if filtros.get('categoria'):
            domain.append(('categ_id.name', 'ilike', filtros['categoria']))
        if filtros.get('ids'):
            domain.append(('id', 'in', filtros['ids']))
        return domain

    def get_productos(self, orden='nombre_asc', limite=10, filtros=None):
        filtros = filtros or {}
        domain = self._build_domain(filtros)

        # Pre-check de volumen con el mismo domain
        count = self.env['product.product'].search_count(domain)
        if count > UMBRAL_REGISTROS:
            return {
                'advertencia': True,
                'cantidad': count,
                'filtros_actuales': filtros,
                'mensaje': (
                    f"Hay {count} productos que coinciden con la consulta. "
                    f"Pedile al usuario que acote la busqueda por nombre, "
                    f"categoria, o rango de precios."
                ),
            }

        order = ORDEN_MAP.get(orden, 'name asc')
        productos = self.env['product.product'].search(domain, limit=limite, order=order)

        data = []
        for p in productos:
            data.append({
                'id': p.id,
                'nombre': p.name,
                'precio': float(p.list_price),
                'stock': float(p.qty_available),
                'categoria': p.categ_id.name if p.categ_id else '',
            })

        return {
            'ids': [d['id'] for d in data],
            'data': data,
            'total': len(data),
            'mensaje': f"Se encontraron {len(data)} productos.",
        }
