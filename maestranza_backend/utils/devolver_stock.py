from django.db import transaction
from inventario.models import Producto

def devolver_stock(venta):
    """
    Devuelve al stock los productos asociados a una venta.
    """
    detalles = venta.detalles.all()
    if not detalles.exists():
        raise Exception("No se encontraron detalles de venta para devolver stock.")

    for detalle in detalles:
        producto = Producto.objects.select_for_update().get(pk=detalle.producto_id)
        print(f"Antes de devolver stock: {producto.nombre}, stock={producto.stock}")
        producto.stock += detalle.cantidad
        producto.save()
        print(f"Después de devolver stock: {producto.nombre}, stock={producto.stock}")

