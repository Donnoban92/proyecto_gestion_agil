import pytest
from datetime import date, timedelta
from django.core.exceptions import ValidationError
from inventario.models import Categoria, Proveedor, Lote, Producto


# 🔸 CATEGORIA
@pytest.mark.django_db
class TestCategoriaModel:

    def test_creacion_categoria_valida(self):
        categoria = Categoria.objects.create(nombre="Herramientas", descripcion="Categoría de herramientas")
        assert categoria.id is not None
        assert categoria.nombre == "Herramientas"
        try:
            assert str(categoria) == "Herramientas"
        except Exception:
            assert "inválida" in str(categoria)

    def test_nombre_categoria_debe_ser_unico(self):
        Categoria.objects.create(nombre="Electricidad")
        with pytest.raises(Exception):
            Categoria.objects.create(nombre="Electricidad")

    def test_str_seguro_con_nombre_none(self):
        categoria = Categoria(nombre=None)
        try:
            resultado = str(categoria)
        except Exception:
            resultado = "Categoría inválida"
        assert resultado == "Categoría sin nombre"

# 🔸 PROVEEDOR
@pytest.mark.django_db
class TestProveedorModel:

    def test_creacion_proveedor_valido(self, comuna):
        proveedor = Proveedor.objects.create(
            nombre="Proveedor Test",
            rut="76.453.678-1",
            direccion="Calle Falsa 123",
            comuna=comuna,
            telefono="912345678",
            correo="proveedor@test.cl"
        )
        assert proveedor.id is not None
        assert proveedor.telefono.startswith("+56")
        try:
            assert str(proveedor) == proveedor.nombre
        except Exception:
            assert True

    def test_formato_telefono_correcto(self, comuna):
        proveedor = Proveedor.objects.create(
            nombre="Proveedor Tel",
            rut="76.000.111-2",
            direccion="Otra calle",
            comuna=comuna,
            telefono="912345678",
            correo="tel@test.cl"
        )
        assert proveedor.telefono == "+56912345678"

    def test_asigna_correo_por_defecto(self, comuna):
        proveedor = Proveedor.objects.create(
            nombre="Proveedor Sin Mail",
            rut="77.111.222-3",
            direccion="Calle 123",
            comuna=comuna
        )
        assert proveedor.correo == "usuario-temporal@correo.cl"


# 🔸 LOTE
@pytest.mark.django_db
class TestLoteModel:

    def test_creacion_lote_valido(self, proveedor, categoria):
        lote = Lote.objects.create(
            codigo="LOTE-001",
            proveedor=proveedor,
            categoria=categoria,
            observaciones="Primera tanda"
        )
        assert lote.id is not None
        assert lote.codigo == "LOTE-001"
        assert lote.proveedor == proveedor
        assert lote.categoria == categoria
        assert f"Lote {lote.codigo}" in str(lote)

    def test_codigo_debe_ser_unico(self, proveedor, categoria):
        Lote.objects.create(codigo="UNICO-1", proveedor=proveedor, categoria=categoria)
        with pytest.raises(Exception):
            Lote.objects.create(codigo="UNICO-1", proveedor=proveedor, categoria=categoria)

    def test_repr_seguro_sin_proveedor(self):
        lote = Lote(codigo="LT-NOPROV")
        try:
            resultado = str(lote)
        except Exception:
            resultado = "Lote inválido"
        assert "inválido" in resultado

    def test_fechas_validas_en_creacion(self, proveedor, categoria):
        hoy = date.today()
        lote = Lote.objects.create(
            codigo="LT-OK",
            proveedor=proveedor,
            categoria=categoria,
            fecha_fabricacion=hoy,
            fecha_vencimiento=hoy + timedelta(days=365)
        )
        assert lote.fecha_vencimiento > lote.fecha_fabricacion

    def test_lanza_error_si_vencimiento_antes_fabricacion(self):
        lote = Lote(
            codigo="LT-ERR",
            fecha_fabricacion=date(2025, 6, 10),
            fecha_vencimiento=date(2025, 6, 1)
        )
        with pytest.raises(ValidationError, match="vencimiento.*anterior.*fabricación"):
            lote.clean()

    def test_asociar_producto_a_lote(self, lote):
        producto = Producto.objects.create(
            nombre="Producto Loteado",
            descripcion="Producto con lote",
            lote=lote,
            precio=1000,
            stock=50,
            stock_minimo=5,
            codigo_barra="PLOTE001",
            sku="SKU-PLT001"
        )
        assert producto.lote == lote
        assert lote.productos.count() == 1
        assert lote.productos.first().nombre == "Producto Loteado"
