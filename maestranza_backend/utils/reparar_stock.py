from django.db import transaction
from inventario.models import Producto

def reparar_stock_venta(venta):
    """
    Corrige de manera segura el stock de productos en base a los detalles de la venta.
    Útil para restaurar inventario cuando se detectan inconsistencias en pruebas o flujo real.
    """
    with transaction.atomic():
        for detalle in venta.detalles.all():
            producto = Producto.objects.select_for_update().get(pk=detalle.producto_id)
            producto.stock += detalle.cantidad
            producto.save()
