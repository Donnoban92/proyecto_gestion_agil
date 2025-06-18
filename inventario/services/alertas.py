from inventario.models import AlertaStock, Producto
from django.utils import timezone
from datetime import timedelta

class AlertaService:
    @staticmethod
    def evaluar_todas():
        """Verifica todos los productos y genera alertas si el stock está bajo el mínimo."""
        productos = Producto.objects.filter(activo=True)
        for producto in productos:
            AlertaService.generar_alerta_si_corresponde(producto)

    @staticmethod
    def generar_alerta_si_corresponde(producto):
        """Crea alerta individual si el producto está bajo stock mínimo."""
        if producto.stock < producto.stock_minimo:
            existe = AlertaStock.objects.filter(producto=producto, activa=True).exists()
            if not existe:
                AlertaStock.objects.create(
                    producto=producto,
                    mensaje=f"Stock bajo para {producto.nombre}. Stock actual: {producto.stock}",
                    activa=True
                )

    @staticmethod
    def marcar_alertas_silenciosas():
        """Cambia el estado de alertas activas que no han sido procesadas después de X tiempo."""
        umbral_tiempo = timezone.now() - timedelta(hours=12)
        AlertaStock.objects.filter(activa=True, fecha_creacion__lt=umbral_tiempo).update(activa=False)
