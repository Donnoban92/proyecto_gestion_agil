from inventario.models import AlertaStock, Producto
from django.utils import timezone
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

class AlertaService:
    @staticmethod
    def evaluar_todas():
        """Verifica todos los productos y genera alertas si el stock está bajo el mínimo."""
        try:
            productos = Producto.objects.filter(activo=True)
            for producto in productos:
                try:
                    AlertaService.generar_alerta_si_corresponde(producto)
                except Exception as e:
                    logger.error(f"Error generando alerta para producto {producto.id}: {str(e)}")
        except Exception as e:
            logger.error(f"Error al obtener productos para evaluación de alertas: {str(e)}")

    @staticmethod
    def generar_alerta_si_corresponde(producto):
        """Crea alerta individual si el producto está bajo stock mínimo."""
        try:
            if producto.stock < producto.stock_minimo:
                existe = AlertaStock.objects.filter(producto=producto, activa=True).exists()
                if not existe:
                    AlertaStock.objects.create(
                        producto=producto,
                        mensaje=f"Stock bajo para {producto.nombre}. Stock actual: {producto.stock}",
                        activa=True
                    )
        except Exception as e:
            logger.error(f"Error al crear alerta para producto {producto.id}: {str(e)}")

    @staticmethod
    def marcar_alertas_silenciosas():
        """Cambia el estado de alertas activas que no han sido procesadas después de X tiempo."""
        try:
            umbral_tiempo = timezone.now() - timedelta(hours=12)
            AlertaStock.objects.filter(activa=True, fecha_creacion__lt=umbral_tiempo).update(activa=False)
        except Exception as e:
            logger.error(f"Error al marcar alertas silenciosas: {str(e)}")
