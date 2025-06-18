from inventario.models import (
    EntradaInventario, SalidaInventario, InventarioFisico,
    Auditoria, Producto, Proveedor, OrdenAutomatica
)
from django.db import transaction
from django.utils import timezone
from inventario.services.auditoria import AuditoriaService
import logging

logger = logging.getLogger(__name__)

class InventarioService:

    @staticmethod
    @transaction.atomic
    def registrar_entrada(producto, cantidad, proveedor, orden=None, precio_unitario=0):
        """Crea una entrada de inventario y actualiza stock, con auditoría."""
        try:
            if not producto or cantidad <= 0:
                raise ValueError("Producto inválido o cantidad no válida.")

            total = cantidad * precio_unitario

            entrada = EntradaInventario.objects.create(
                producto=producto,
                proveedor=proveedor,
                orden=orden,
                cantidad=cantidad,
                precio_unitario=precio_unitario,
                total=total,
            )

            producto.stock += cantidad
            producto.save(update_fields=["stock"])

            AuditoriaService.registrar(
                usuario=None,
                modelo="EntradaInventario",
                id_objeto=entrada.id,
                accion="crear",
                descripcion=f"Entrada de {cantidad} unidades para '{producto.nombre}'"
            )

            return entrada

        except Exception as e:
            logger.error(f"Error al registrar entrada de inventario para producto {getattr(producto, 'id', 'N/A')}: {str(e)}")
            raise

    @staticmethod
    @transaction.atomic
    def registrar_salida(producto, cantidad, responsable, motivo, observacion=""):
        """Registra una salida de inventario validando stock y actualiza con auditoría."""
        try:
            if not producto or cantidad <= 0:
                raise ValueError("Producto inválido o cantidad no válida.")
            if producto.stock < cantidad:
                raise ValueError("No hay stock suficiente para realizar la salida.")

            salida = SalidaInventario.objects.create(
                producto=producto,
                cantidad=cantidad,
                responsable=responsable,
                motivo=motivo,
                observacion=observacion
            )

            producto.stock -= cantidad
            producto.save(update_fields=["stock"])

            AuditoriaService.registrar(
                usuario=responsable,
                modelo="SalidaInventario",
                id_objeto=salida.id,
                accion="crear",
                descripcion=f"Salida de {cantidad} unidades de '{producto.nombre}' (motivo: {motivo})"
            )

            return salida

        except Exception as e:
            logger.error(f"Error al registrar salida de inventario para producto {getattr(producto, 'id', 'N/A')}: {str(e)}")
            raise

    @staticmethod
    @transaction.atomic
    def registrar_conteo_fisico(producto, stock_real, responsable):
        """Registra un conteo físico del inventario con cálculo de diferencia."""
        try:
            if stock_real < 0:
                raise ValueError("El stock real no puede ser negativo.")

            conteo = InventarioFisico.objects.create(
                producto=producto,
                stock_real=stock_real,
                responsable=responsable,
                diferencia=stock_real - producto.stock
            )

            AuditoriaService.registrar(
                usuario=responsable,
                modelo="InventarioFisico",
                id_objeto=conteo.id,
                accion="crear",
                descripcion=f"Conteo físico de '{producto.nombre}': stock real {stock_real}, diferencia {conteo.diferencia}"
            )

            return conteo

        except Exception as e:
            logger.error(f"Error al registrar conteo físico para producto {getattr(producto, 'id', 'N/A')}: {str(e)}")
            raise
