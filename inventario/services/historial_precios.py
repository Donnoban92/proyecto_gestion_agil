from inventario.models import HistorialPrecioProducto
from django.utils import timezone

class PrecioService:
    @staticmethod
    def registrar_precio(producto, proveedor, precio):
        """Guarda histórico si cambió el precio."""
        ultimo = PrecioService.obtener_ultimo_precio(producto, proveedor)
        if not ultimo or ultimo.precio != precio:
            HistorialPrecioProducto.objects.create(
                producto=producto,
                proveedor=proveedor,
                precio=precio,
                fecha=timezone.now()
            )

    @staticmethod
    def obtener_ultimo_precio(producto, proveedor):
        """Consulta precio más reciente registrado."""
        return (
            HistorialPrecioProducto.objects
            .filter(producto=producto, proveedor=proveedor)
            .order_by("-fecha")
            .first()
        )
