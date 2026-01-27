from odoo import fields
from dateutil.relativedelta import relativedelta


def month_range(record):
    """Retorna (primer_dia_mes_actual, primer_dia_mes_siguiente)"""
    today = fields.Date.context_today(record)
    start = today.replace(day=1)
    end = start + relativedelta(months=1)
    return start, end


def prev_month_range(record):
    """Retorna (primer_dia_mes_anterior, primer_dia_mes_actual)"""
    today = fields.Date.context_today(record)
    start_this = today.replace(day=1)
    start_prev = start_this - relativedelta(months=1)
    return start_prev, start_this


def today(record):
    """Retorna la fecha de hoy respetando timezone del usuario"""
    return fields.Date.context_today(record)


def variacion_porcentual(actual, anterior):
    """Calcula variación porcentual entre dos valores"""
    if anterior == 0:
        if actual == 0:
            return 0
        return 100.0
    return round(((actual - anterior) / anterior) * 100, 1)
