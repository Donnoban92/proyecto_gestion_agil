from inventario.models import OrdenAutomatica, AlertaStock, EntradaInventario, CotizacionProveedor
from inventario.services.notificaciones import NotificacionService
from inventario.services.inventario import InventarioService
from maestranza_backend.utils.logger import audit_logger
from django.db import transaction
from django.core.exceptions import ValidationError
import logging

logger = logging.getLogger(__name__)

class OrdenService:
    @staticmethod
    @transaction.atomic
    def crear_orden_desde_alerta(alerta: AlertaStock):
        try:
            if not alerta or alerta.estado not in ["activa", "pendiente"]:
                raise ValidationError("La alerta no está en un estado válido para generar una orden.")

            if alerta.usada:
                raise ValidationError("Esta alerta ya ha sido utilizada para generar una orden.")

            producto = alerta.producto
            lote = producto.lote
            proveedor = lote.proveedor

            if not proveedor:
                raise ValidationError("El producto no tiene proveedor asignado a su lote.")

            orden = OrdenAutomatica.objects.create(
                alerta=alerta,
                producto=producto,
                proveedor=proveedor,
                cantidad_ordenada=alerta.stock_sugerido or producto.stock_minimo,
                estado="pendiente"
            )

            alerta.usada = True
            alerta.orden_relacionada = orden
            alerta.save(update_fields=["usada", "orden_relacionada"])

            NotificacionService.notificar_roles(
                f"📦 Se ha generado una nueva orden automática para el producto '{producto.nombre}' (stock actual: {producto.stock}).",
                roles=["admin", "inventario"]
            )

            audit_logger.info(f"✅ Orden automática #{orden.id} generada desde alerta #{alerta.id} por servicio.")

            return orden

        except Exception as e:
            logger.error(f"Error al crear orden desde alerta {getattr(alerta, 'id', 'N/A')}: {str(e)}")
            raise

    @staticmethod
    @transaction.atomic
    def generar_entrada_si_orden_confirmada(orden: OrdenAutomatica):
        try:
            if not orden or orden.estado != "completada":
                return None  # No hacer nada si no está completada

            ya_existe = EntradaInventario.objects.filter(orden=orden).exists()
            if ya_existe:
                return None  # Ya se generó la entrada antes

            producto = orden.producto
            cantidad = orden.cantidad_ordenada
            proveedor = orden.proveedor

            entrada = InventarioService.registrar_entrada(
                producto=producto,
                cantidad=cantidad,
                proveedor=proveedor,
                orden=orden,
                precio_unitario=producto.precio_actual or 0
            )

            audit_logger.info(f"✅ Entrada generada automáticamente por orden #{orden.id}.")

            return entrada

        except Exception as e:
            logger.error(f"Error al generar entrada para orden {getattr(orden, 'id', 'N/A')}: {str(e)}")
            raise

    @staticmethod
    @transaction.atomic
    def crear_cotizaciones_por_proveedor(orden: OrdenAutomatica):
        try:
            if not orden or orden.estado != "pendiente":
                raise ValidationError("La orden no está en estado válido para generar cotizaciones.")

            cotizacion, creado = CotizacionProveedor.objects.get_or_create(
                orden=orden,
                defaults={
                    "proveedor": orden.proveedor,
                    "precio_unitario": orden.producto.precio_actual or 0,
                    "archivo_pdf": None,  # será generado después
                }
            )

            if creado:
                NotificacionService.notificar_roles(
                    f"📄 Se ha creado una cotización para la orden #{orden.id} con el proveedor '{orden.proveedor.nombre}'.",
                    roles=["compras"]
                )
                audit_logger.info(f"📝 Cotización creada para orden #{orden.id} - proveedor: {orden.proveedor.nombre}")
            else:
                audit_logger.info(f"ℹ️ Cotización ya existente para orden #{orden.id}")

            return cotizacion

        except Exception as e:
            logger.error(f"Error al crear cotizaciones para orden {getattr(orden, 'id', 'N/A')}: {str(e)}")
            raise
