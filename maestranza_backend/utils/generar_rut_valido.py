import random

def generar_rut_valido():
    """Genera un RUT chileno válido con DV (sin puntos, con guion)"""
    cuerpo = random.randint(10_000_000, 24_000_000)  # rango realista
    suma = 0
    multiplicador = 2

    for digito in reversed(str(cuerpo)):
        suma += int(digito) * multiplicador
        multiplicador = 2 if multiplicador == 7 else multiplicador + 1

    resto = 11 - (suma % 11)
    if resto == 11:
        dv = "0"
    elif resto == 10:
        dv = "K"
    else:
        dv = str(resto)

    return f"{cuerpo}-{dv}"
