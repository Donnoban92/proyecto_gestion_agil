from inventario.models import AlertaStock, Producto

UMBRAL_STOCK_MINIMO = 20

def crear_alerta_stock(producto):
    """Crea alerta solo si: stock <= 20 Y no existe alerta activa."""
    if producto.stock > UMBRAL_STOCK_MINIMO:
        return False
    
    # Verifica si YA EXISTE una alerta activa (evita duplicados)
    existe_alerta = AlertaStock.objects.filter(
        producto=producto,
        estado="activa"
    ).exists()
    
    if not existe_alerta:
        AlertaStock.objects.create(
            producto=producto,
            estado="activa"
        )
        return True
    return False