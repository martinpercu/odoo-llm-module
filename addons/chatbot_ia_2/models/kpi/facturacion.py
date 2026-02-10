from odoo import models
from dateutil.relativedelta import relativedelta
from .helpers import today, UMBRAL_REGISTROS


class KPIFacturacion2(models.AbstractModel):
    _name = 'chatbot2.kpi.facturacion'
    _description = 'KPI Facturacion para Chatbot v2'

    def _build_domain(self, tipo, estado, dias_vencimiento, cliente_ids):
        """Construye el domain para facturas."""
        hoy = today(self)
        move_type = 'out_invoice' if tipo == 'cliente' else 'in_invoice'
        domain = [
            ('move_type', '=', move_type),
            ('state', '=', 'posted'),
        ]

        if estado == 'pendiente':
            domain.append(('payment_state', 'in', ['not_paid', 'partial']))
            if dias_vencimiento:
                fecha_limite = hoy + relativedelta(days=dias_vencimiento)
                domain += [
                    ('invoice_date_due', '>=', hoy),
                    ('invoice_date_due', '<=', fecha_limite),
                ]
        elif estado == 'vencido':
            domain += [
                ('payment_state', 'in', ['not_paid', 'partial']),
                ('invoice_date_due', '<', hoy),
            ]
        elif estado == 'pagado':
            domain.append(('payment_state', '=', 'paid'))
        # 'todos' = sin filtro adicional de payment_state

        if cliente_ids:
            domain.append(('partner_id', 'in', cliente_ids))

        return domain

    def get_facturas(self, tipo='cliente', estado='pendiente',
                     dias_vencimiento=None, cliente_ids=None, limite=20):
        domain = self._build_domain(tipo, estado, dias_vencimiento, cliente_ids)

        # Pre-check de volumen con el mismo domain
        count = self.env['account.move'].search_count(domain)
        if count > UMBRAL_REGISTROS:
            tipo_label = 'cliente' if tipo == 'cliente' else 'proveedor'
            return {
                'advertencia': True,
                'cantidad': count,
                'filtros_actuales': {
                    'tipo': tipo,
                    'estado': estado,
                    'dias_vencimiento': dias_vencimiento,
                    'cliente_ids': cliente_ids,
                },
                'mensaje': (
                    f"Hay {count} facturas de {tipo_label} con estado '{estado}'. "
                    f"Pedile al usuario que acote la busqueda por estado "
                    f"(pendiente, vencido, pagado), cliente, o dias de vencimiento."
                ),
            }

        facturas = self.env['account.move'].search(
            domain, limit=limite, order='invoice_date_due asc'
        )

        data = []
        for f in facturas:
            data.append({
                'id': f.id,
                'numero': f.name,
                'cliente': f.partner_id.name,
                'cliente_id': f.partner_id.id,
                'monto_total': float(f.amount_total),
                'monto_pendiente': float(f.amount_residual),
                'fecha_vencimiento': str(f.invoice_date_due) if f.invoice_date_due else '',
                'estado_pago': f.payment_state,
            })

        total_pendiente = sum(d['monto_pendiente'] for d in data)
        tipo_label = 'cliente' if tipo == 'cliente' else 'proveedor'

        return {
            'ids': [d['id'] for d in data],
            'data': data,
            'total_pendiente': total_pendiente,
            'count': len(data),
            'tipo': tipo,
            'estado': estado,
            'mensaje': (
                f"Se encontraron {len(data)} facturas de {tipo_label} "
                f"({estado}) por un total pendiente de ${total_pendiente:,.2f}"
            ),
        }
