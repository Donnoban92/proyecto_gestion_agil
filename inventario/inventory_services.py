from datetime import datetime
from django.utils import timezone
from django.db.models import Sum, F, Q, Value
from .models import (
    AlertaStock, Producto, OrdenAutomatica, Kit, KitItem,
    InventarioFisico, HistorialPrecioProducto, EntradaInventario,
    SalidaInventario, Notificacion, Auditoria, CustomUser, CotizacionProveedor
)


# === 1. Servicio: Verificación de bajo stock ===
def verificar_stock_bajo():
    productos = Producto.objects.filter(stock__lte=F('stock_minimo'))
    for producto in productos:
        if not AlertaStock.objects.filter(producto=producto, activa=True).exists():
            AlertaStock.objects.create(
                producto=producto,
                mensaje=f"Stock bajo para {producto.nombre}",
                tipo='bajo_stock'
            )


# === 2. Servicio: Generación de orden automática desde alerta ===
def generar_orden_automatica(alerta):
    producto = alerta.producto
    proveedor = producto.proveedor
    cantidad = producto.stock_minimo * 2

    return OrdenAutomatica.objects.create(
        alerta=alerta,
        producto=producto,
        proveedor=proveedor,
        cantidad_ordenada=cantidad
    )


# === 3. Servicio: Verificar silencio de alertas ===
def verificar_silencio_alertas(dias=2):
    desde = timezone.now() - timezone.timedelta(days=dias)
    alertas = AlertaStock.objects.filter(activa=True, fecha_creacion__lte=desde)
    for alerta in alertas:
        Notificacion.objects.create(
            usuario=CustomUser.objects.filter(is_superuser=True).first(),
            mensaje=f"Alerta silenciosa sin resolución: {alerta.mensaje}"
        )


# === 4. Servicio: Generar Kit completo ===
def generar_kit(nombre, descripcion, productos_cantidades):
    kit = Kit.objects.create(nombre=nombre, descripcion=descripcion)
    for producto, cantidad in productos_cantidades:
        KitItem.objects.create(kit=kit, producto=producto, cantidad=cantidad)
    return kit


# === 5. Servicio: Actualizar historial de precio ===
def registrar_precio_producto(producto, proveedor, precio):
    if producto and proveedor and precio > 0:
        HistorialPrecioProducto.objects.create(
            producto=producto,
            proveedor=proveedor,
            precio=precio
        )


# === 6. Servicio: Generar entrada de inventario ===
def registrar_entrada(producto, cantidad, responsable, observacion=""):
    EntradaInventario.objects.create(
        producto=producto,
        cantidad=cantidad,
        responsable=responsable,
        observacion=observacion
    )
    producto.stock += cantidad
    producto.save()


# === 7. Servicio: Generar salida de inventario ===
def registrar_salida(producto, cantidad, responsable, motivo="uso", observacion=""):
    if producto.stock >= cantidad:
        SalidaInventario.objects.create(
            producto=producto,
            cantidad=cantidad,
            responsable=responsable,
            motivo=motivo,
            observacion=observacion
        )
        producto.stock -= cantidad
        producto.save()


# === 8. Servicio: Generar auditoría ===
def registrar_accion(usuario, modelo, objeto_id, accion, descripcion):
    Auditoria.objects.create(
        usuario=usuario,
        modelo_afectado=modelo,
        id_objeto=objeto_id,
        accion=accion,
        descripcion=descripcion
    )


# === 9. Servicio: Notificar a usuario ===
def notificar_usuario(usuario, mensaje):
    Notificacion.objects.create(usuario=usuario, mensaje=mensaje)
