from celery import shared_task
from models import AlertaStock
from .services.alertas import AlertaService
from .services.ordenes import OrdenService
from maestranza_backend.utils.logger import audit_logger
import logging
logger = logging.getLogger("audit")

@shared_task
def verificar_alertas_stock_bajo():
    AlertaService.evaluar_todas()
    audit_logger.info("✅ Verificación de stock bajo ejecutada por Celery.")

@shared_task
def verificar_alertas_sin_respuesta():
    AlertaService.marcar_alertas_silenciosas()
    audit_logger.info("🔕 Verificación de alertas sin respuesta ejecutada.")


@shared_task
def prueba_tarea():
    print("✅ Celery está funcionando correctamente.")
    return True

@shared_task
def tarea_generar_ordenes_desde_alertas():
    pendientes = AlertaStock.objects.filter(
        estado__in=["activa", "pendiente"],
        usada=False,
        orden_relacionada__isnull=True
    )
    for alerta in pendientes:
        try:
            OrdenService.crear_orden_desde_alerta(alerta)
        except Exception as e:
            logger.error(f"❌ Falló la creación de orden desde alerta #{alerta.id}: {e}")
