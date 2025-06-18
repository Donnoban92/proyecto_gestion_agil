from inventario.models import (
    EntradaInventario,
    SalidaInventario,
    InventarioFisico,
    Auditoria,
    Producto,
    Proveedor,
)
from django.db import transaction
from inventario.services.auditoria import AuditoriaService


class InventarioService:
    @staticmethod
    def registrar_entrada(producto, cantidad, proveedor, orden=None, precio_unitario=0):
        """Actualiza stock, crea entrada y registra auditoría."""

    @staticmethod
    def registrar_salida(producto, cantidad, responsable, motivo, observacion=""):
        """Valida stock y registra salida con auditoría."""

    @staticmethod
    def registrar_conteo_fisico(producto, stock_real, responsable):
        """Crea `InventarioFisico` y evalúa diferencia."""
