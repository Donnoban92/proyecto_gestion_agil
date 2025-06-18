from ...inventario.models import Proveedor


def proveedor_default():
    return Proveedor.objects.first().id if Proveedor.objects.exists() else None
