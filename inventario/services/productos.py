from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum
from inventario.models import Producto, SalidaInventario
import logging

logger = logging.getLogger(__name__)

class ProductoService:
    @staticmethod
    def actualizar_stock(producto, cantidad, modo="entrada"):
        """Suma o resta stock del producto."""
        try:
            if not producto:
                raise ValueError("Producto no válido.")

            if cantidad < 0:
                raise ValueError("La cantidad no puede ser negativa.")

            if modo == "entrada":
                producto.stock += cantidad
            elif modo == "salida":
                if producto.stock < cantidad:
                    raise ValueError("Stock insuficiente para la salida.")
                producto.stock -= cantidad
            else:
                raise ValueError("Modo no reconocido. Usa 'entrada' o 'salida'.")

            producto.save()
            return producto.stock
        except Exception as e:
            logger.error(f"Error al actualizar stock para producto {getattr(producto, 'id', 'N/A')}: {str(e)}")
            raise

    @staticmethod
    def obtener_stock_actual(producto_id):
        """Devuelve el stock actual de un producto."""
        try:
            producto = Producto.objects.get(id=producto_id)
            return producto.stock
        except Producto.DoesNotExist:
            logger.error(f"Producto con id {producto_id} no existe.")
            return None
        except Exception as e:
            logger.error(f"Error al obtener stock actual para producto {producto_id}: {str(e)}")
            return None

    @staticmethod
    def calcular_consumo_promedio(producto_id, dias=30):
        """Para proyectar necesidades futuras."""
        try:
            producto = Producto.objects.get(id=producto_id)
            fecha_inicio = timezone.now() - timedelta(days=dias)
            salidas = SalidaInventario.objects.filter(producto=producto, fecha__gte=fecha_inicio)

            total_consumido = salidas.aggregate(total=Sum("cantidad"))["total"] or 0
            promedio_diario = total_consumido / dias
            return round(promedio_diario, 2)
        except Producto.DoesNotExist:
            logger.error(f"Producto con id {producto_id} no existe.")
            return 0
        except Exception as e:
            logger.error(f"Error al calcular consumo promedio para producto {producto_id}: {str(e)}")
            return 0
