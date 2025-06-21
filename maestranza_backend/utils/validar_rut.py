import re

def validar_rut(rut: str) -> bool:
    """
    Valida un RUT chileno con formato 12.345.678-5
    - Acepta puntos y guion.
    - Verifica el dígito verificador correctamente.
    """
    try:
        rut = rut.replace(".", "").replace("-", "").upper()
        cuerpo, dv_ingresado = rut[:-1], rut[-1]

        if not cuerpo.isdigit():
            return False

        suma = 0
        multiplicador = 2
        for digito in reversed(cuerpo):
            suma += int(digito) * multiplicador
            multiplicador = 2 if multiplicador == 7 else multiplicador + 1

        resto = 11 - (suma % 11)
        if resto == 11:
            dv_calculado = "0"
        elif resto == 10:
            dv_calculado = "K"
        else:
            dv_calculado = str(resto)

        return dv_ingresado == dv_calculado
    except Exception:
        return False
