from inventario.models import Kit, KitItem, Producto
from django.db import transaction
from django.core.exceptions import ValidationError

class KitService:
    @staticmethod
    def crear_kit(nombre, descripcion, items):
        """
        Crea un nuevo kit y sus ítems asociados.
        items: lista de diccionarios con claves 'producto_id' y 'cantidad'
        """
        KitService.validar_items_sin_duplicados(items)

        with transaction.atomic():
            kit = Kit.objects.create(nombre=nombre.strip(), descripcion=descripcion.strip())
            for item in items:
                producto_id = item.get("producto_id")
                cantidad = item.get("cantidad")
                if not producto_id or cantidad is None:
                    raise ValidationError("Cada ítem debe incluir producto_id y cantidad.")
                producto = Producto.objects.get(id=producto_id)
                KitItem.objects.create(kit=kit, producto=producto, cantidad=cantidad)
            return kit

    @staticmethod
    def validar_items_sin_duplicados(items):
        """
        Verifica que no haya productos duplicados en la lista de ítems.
        """
        productos_ids = [item.get("producto_id") for item in items]
        if len(productos_ids) != len(set(productos_ids)):
            raise ValidationError("No se permiten productos duplicados dentro del kit.")
