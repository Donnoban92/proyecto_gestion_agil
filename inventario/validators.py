from django.core.exceptions import ValidationError
from datetime import date

def validar_precio_positivo(value):
    """
    Valida que el precio sea mayor a cero.
    """
    if value <= 0:
        raise ValidationError("El precio debe ser mayor que cero.")
    return value

def validar_stock_no_negativo(value):
    """
    Valida que el stock no sea negativo.
    """
    if value < 0:
        raise ValidationError("El stock no puede ser negativo.")
    return value

def validar_stock_minimo_no_negativo(value):
    """
    Valida que el stock mínimo no sea negativo.
    """
    if value < 0:
        raise ValidationError("El stock mínimo no puede ser negativo.")
    return value

def validar_codigo_barra(value):
    """
    Valida que el código de barra tenga al menos 8 dígitos numéricos.
    """
    if not value.isdigit() or len(value) < 8:
        raise ValidationError("El código de barra debe contener al menos 8 dígitos numéricos.")
    return value

def validar_sku_formato(value):
    """
    Valida que el SKU tenga un formato aceptable (alfa-numérico).
    """
    if not value or len(value.strip()) < 4:
        raise ValidationError("El SKU debe tener al menos 4 caracteres.")
    return value.upper()

def validar_fecha_fabricacion(fecha_fabricacion):
    """
    Valida que la fecha de fabricación no sea futura.
    """
    if fecha_fabricacion > date.today():
        raise ValidationError("La fecha de fabricación no puede ser futura.")
    return fecha_fabricacion

def validar_fechas_lote(fecha_fab, fecha_venc):
    """
    Valida que la fecha de vencimiento sea posterior a la de fabricación.
    """
    if fecha_fab and fecha_venc and fecha_venc <= fecha_fab:
        raise ValidationError("La fecha de vencimiento debe ser posterior a la de fabricación.")
    return fecha_fab, fecha_venc

