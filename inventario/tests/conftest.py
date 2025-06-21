import pytest
from maestranza_backend.utils.generar_rut_valido import generar_rut_valido
from inventario.models import (
    Categoria, Proveedor, Producto, Lote, AlertaStock, OrdenAutomatica,
    EntradaInventario, SalidaInventario, CustomUser, Kit, KitItem,
    HistorialPrecioProducto, Notificacion, Auditoria, InventarioFisico, CotizacionProveedor,
    Comuna, Region, Ciudad, Pais, Cargo
)
from django.utils import timezone
from django.contrib.auth.hashers import make_password

@pytest.fixture
def categoria():
    return Categoria.objects.create(nombre="Categoría Test")

@pytest.fixture
def proveedor(comuna):
    return Proveedor.objects.create(
        nombre="Proveedor Test",
        rut="76.123.456-7",
        direccion="Calle Falsa 123",
        comuna=comuna,
        telefono="+56911112222",
        correo="proveedor@test.cl"
    )

@pytest.fixture
def usuario_admin(db, comuna):
    return CustomUser.objects.create(
        username="admin",
        email="admin@test.com",
        password=make_password("adminpass123"),
        rut=generar_rut_valido(),
        comuna=comuna,
        telefono="+56912345678"
    )

@pytest.fixture
def producto(categoria, proveedor):
    lote = Lote.objects.create(
        codigo="L001",
        proveedor=proveedor,
        categoria=categoria,
        fecha_fabricacion="2024-01-01",
        fecha_vencimiento="2025-01-01"
    )
    return Producto.objects.create(
        nombre="Producto Test",
        descripcion="Producto de prueba",
        lote=lote,
        precio=1000,
        stock=15,
        stock_minimo=5,
        codigo_barra="12345678",
        sku="SKU-TEST"
    )

@pytest.fixture
def producto_con_stock_bajo(categoria, proveedor):
    return Producto.objects.create(
        nombre="Producto Bajo",
        descripcion="Stock bajo",
        categoria=categoria,
        proveedor=proveedor,
        stock=2,
        stock_minimo=10
    )

@pytest.fixture
def lote(categoria, proveedor):
    return Lote.objects.create(
        codigo="LT123",
        proveedor=proveedor,
        categoria=categoria,
        fecha_vencimiento=timezone.now() + timezone.timedelta(days=365)
    )

@pytest.fixture
def alerta(producto):
    return AlertaStock.objects.create(
        producto=producto,
        estado="pendiente"
    )

@pytest.fixture
def orden(alerta, producto, proveedor):
    return OrdenAutomatica.objects.create(
        alerta=alerta,
        producto=producto,
        proveedor=proveedor,
        cantidad_ordenada=10
    )

@pytest.fixture
def entrada(producto, proveedor):
    return EntradaInventario.objects.create(
        producto=producto,
        proveedor=proveedor,
        cantidad=10
    )

@pytest.fixture
def salida(producto, usuario_admin):
    return SalidaInventario.objects.create(
        producto=producto,
        cantidad=5,
        motivo="Uso interno",
        responsable=usuario_admin
    )

@pytest.fixture
def kit(producto):
    return Kit.objects.create(
        nombre="Kit Básico",
        descripcion="Incluye un solo producto de prueba"
    )

@pytest.fixture
def kititem(kit, producto):
    return KitItem.objects.create(
        kit=kit,
        producto=producto,
        cantidad=1
    )

@pytest.fixture
def historial_precio(producto, proveedor):
    return HistorialPrecioProducto.objects.create(
        producto=producto,
        proveedor=proveedor,
        precio=1000
    )

@pytest.fixture
def notificacion(usuario_admin):
    return Notificacion.objects.create(
        mensaje="Prueba de notificación",
        usuario=usuario_admin
    )

@pytest.fixture
def auditoria(usuario_admin):
    return Auditoria.objects.create(
        usuario=usuario_admin,
        accion="CREAR",
        modelo_afectado="Producto",
        descripcion="Se creó un producto de prueba"
    )

@pytest.fixture
def inventario_fisico(producto, usuario_admin):
    return InventarioFisico.objects.create(
        producto=producto,
        stock_real=15,
        responsable=usuario_admin
    )

@pytest.fixture
def cotizacion(orden):
    return CotizacionProveedor.objects.create(
        orden=orden,
        monto=50000,
        estado="pendiente"
    )

@pytest.fixture
def comuna(ciudad):
    return Comuna.objects.create(nombre="Comuna Test", ciudad=ciudad)

@pytest.fixture
def ciudad(region):
    return Ciudad.objects.create(nombre="Ciudad Test", region=region)

@pytest.fixture
def region(pais):
    return Region.objects.create(nombre="Región Test", pais=pais)

@pytest.fixture
def pais():
    return Pais.objects.create(nombre="Chile")

import pytest
from inventario.models import Cargo

@pytest.fixture
def cargo():
    return Cargo.objects.create(nombre="Gestor de Inventario")

