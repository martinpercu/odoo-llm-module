from odoo import fields
from dateutil.relativedelta import relativedelta


def month_range(record):
    """Retorna (primer_dia_mes_actual, primer_dia_mes_siguiente)"""
    hoy = fields.Date.context_today(record)
    start = hoy.replace(day=1)
    end = start + relativedelta(months=1)
    return start, end


def prev_month_range(record):
    """Retorna (primer_dia_mes_anterior, primer_dia_mes_actual)"""
    hoy = fields.Date.context_today(record)
    start_this = hoy.replace(day=1)
    start_prev = start_this - relativedelta(months=1)
    return start_prev, start_this


def quarter_range(record):
    """Retorna (primer_dia_trimestre_actual, primer_dia_trimestre_siguiente)"""
    hoy = fields.Date.context_today(record)
    quarter_start_month = ((hoy.month - 1) // 3) * 3 + 1
    start = hoy.replace(month=quarter_start_month, day=1)
    end = start + relativedelta(months=3)
    return start, end


def year_range(record):
    """Retorna (1 enero actual, 1 enero siguiente)"""
    hoy = fields.Date.context_today(record)
    start = hoy.replace(month=1, day=1)
    end = start + relativedelta(years=1)
    return start, end


def date_range_from_periodo(record, periodo):
    """Convierte un string de periodo a tupla (fecha_inicio, fecha_fin)"""
    if periodo == 'mes_actual':
        return month_range(record)
    elif periodo == 'mes_anterior':
        return prev_month_range(record)
    elif periodo == 'trimestre':
        return quarter_range(record)
    elif periodo == 'anio':
        return year_range(record)
    return month_range(record)


def today(record):
    """Retorna la fecha de hoy respetando timezone del usuario"""
    return fields.Date.context_today(record)
