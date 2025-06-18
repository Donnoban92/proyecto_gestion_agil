from inventario.models import HistorialPrecioProducto
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)

class PrecioService:
    @staticmethod
    def registrar_precio(producto, proveedor, precio):
        """Guarda histórico si cambió el precio."""
        try:
            ultimo = PrecioService.obtener_ultimo_precio(producto, proveedor)
            if not ultimo or ultimo.precio != precio:
                HistorialPrecioProducto.objects.create(
                    producto=producto,
                    proveedor=proveedor,
                    precio=precio,
                    fecha=timezone.now()
                )
        except Exception as e:
            logger.error(f"Error al registrar precio para producto {producto.id}: {str(e)}")

    @staticmethod
    def obtener_ultimo_precio(producto, proveedor):
        """Consulta precio más reciente registrado."""
        try:
            return (
                HistorialPrecioProducto.objects
                .filter(producto=producto, proveedor=proveedor)
                .order_by("-fecha")
                .first()
            )
        except Exception as e:
            logger.error(f"Error al obtener último precio para producto {producto.id}: {str(e)}")
            return None
