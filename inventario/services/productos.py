from datetime import timedelta
from django.utils import timezone
from django.db.models import Sum
from inventario.models import Producto, SalidaInventario


class ProductoService:
    @staticmethod
    def actualizar_stock(producto, cantidad, modo="entrada"):
        """Suma o resta stock del producto."""
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

    @staticmethod
    def obtener_stock_actual(producto_id):
        """Devuelve el stock actual de un producto."""
        producto = Producto.objects.get(id=producto_id)
        return producto.stock

    @staticmethod
    def calcular_consumo_promedio(producto_id, dias=30):
        """Para proyectar necesidades futuras."""
        producto = Producto.objects.get(id=producto_id)
        fecha_inicio = timezone.now() - timedelta(days=dias)
        salidas = SalidaInventario.objects.filter(producto=producto, fecha__gte=fecha_inicio)

        total_consumido = salidas.aggregate(total=Sum("cantidad"))["total"] or 0
        promedio_diario = total_consumido / dias
        return round(promedio_diario, 2)
