from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from inventario.models import AlertaStock, Producto, EntradaInventario, SalidaInventario, Kit
from inventario.services.ordenes import OrdenService
import logging

logger = logging.getLogger("audit")


@receiver(post_save, sender=AlertaStock)
def generar_orden_automatica_si_corresponde(sender, instance, created, **kwargs):
    try:
        if instance.estado in ["activa", "pendiente"] and not instance.usada and not instance.orden_relacionada:
            OrdenService.crear_orden_desde_alerta(instance)
    except Exception as e:
        logger.error(f"❌ Error al generar orden automática desde alerta #{instance.id}: {e}")
