from decimal import Decimal, InvalidOperation

def to_decimal_safe(value):
    """
    Convierte de manera segura un número a Decimal.
    Si no puede convertirlo, lanza un ValueError.
    """
    try:
        if isinstance(value, Decimal):
            return value
        return Decimal(str(value))
    except (ValueError, TypeError, InvalidOperation):
        raise ValueError(f"Valor inválido para conversión a Decimal: {value}")
    
def to_int_safe(value):
    """
    Convierte de manera segura un número a int.
    Si es Decimal o float, lo redondea correctamente.
    """
    try:
        if isinstance(value, int):
            return value
        return int(round(float(value)))
    except (ValueError, TypeError):
        raise ValueError(f"Valor inválido para conversión a int: {value}")
    
def format_number_cl(value):
    """
    Formatea un número entero como string usando el punto (.) como separador de miles.
    Ejemplo: 12345 -> '12.345'
    """
    try:
        return f"{int(value):,}".replace(",", ".")
    except (ValueError, TypeError):
        raise ValueError(f"Valor inválido para formato chileno: {value}")
    
def round_to_nearest_ten(value):
    """Redondea un número al múltiplo de 10 más cercano."""
    return int(round(value / 10.0) * 10)

def round_normal(value):
    """Redondea un número normal a entero."""
    return int(round(value))


