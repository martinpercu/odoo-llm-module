from odoo import models
from dateutil.relativedelta import relativedelta
from .helpers import today


class KPIFacturacion(models.AbstractModel):
    _name = 'chatbot.kpi.facturacion'
    _description = 'KPIs de Facturación para Chatbot'

    def get_cuentas_por_cobrar_vencidas(self):
        """KPI 5: Facturas de cliente vencidas pendientes de cobro"""
        hoy = today(self)

        facturas = self.env['account.move'].search([
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('payment_state', 'in', ['not_paid', 'partial']),
            ('invoice_date_due', '<', hoy),
        ])

        total = sum(facturas.mapped('amount_residual'))
        cantidad = len(facturas)

        return {
            'total_pendiente': total,
            'cantidad_facturas': cantidad,
            'mensaje': (
                f"Tienes {cantidad} facturas de cliente vencidas "
                f"por un total de ${total:,.2f} pendiente de cobro"
            )
        }

    def get_cuentas_por_pagar_vencidas(self):
        """KPI 6: Facturas de proveedor vencidas pendientes de pago"""
        hoy = today(self)

        facturas = self.env['account.move'].search([
            ('move_type', '=', 'in_invoice'),
            ('state', '=', 'posted'),
            ('payment_state', 'in', ['not_paid', 'partial']),
            ('invoice_date_due', '<', hoy),
        ])

        total = sum(facturas.mapped('amount_residual'))
        cantidad = len(facturas)

        return {
            'total_pendiente': total,
            'cantidad_facturas': cantidad,
            'mensaje': (
                f"Tienes {cantidad} facturas de proveedor vencidas "
                f"por un total de ${total:,.2f} pendiente de pago"
            )
        }

    def get_por_cobrar_proximos_dias(self, dias=10):
        """KPI 7: Monto a percibir en los próximos X días"""
        hoy = today(self)
        fecha_fin = hoy + relativedelta(days=dias)

        facturas = self.env['account.move'].search([
            ('move_type', '=', 'out_invoice'),
            ('state', '=', 'posted'),
            ('payment_state', 'in', ['not_paid', 'partial']),
            ('invoice_date_due', '>=', hoy),
            ('invoice_date_due', '<=', fecha_fin),
        ])

        total = sum(facturas.mapped('amount_residual'))
        cantidad = len(facturas)

        return {
            'total_por_cobrar': total,
            'cantidad_facturas': cantidad,
            'dias': dias,
            'mensaje': (
                f"En los próximos {dias} días tienes {cantidad} facturas "
                f"por cobrar por un total de ${total:,.2f}"
            )
        }
