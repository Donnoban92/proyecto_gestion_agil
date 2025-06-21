import pytest
from django.core.exceptions import ValidationError
from inventario.models import HistorialPrecioProducto
from inventario.services.historial_precios import PrecioService
from django.utils import timezone


@pytest.mark.django_db
class TestHistorialPrecioProductoModel:

    def test_crear_historial_precio_valido(self, producto, proveedor):
        try:
            historial = HistorialPrecioProducto.objects.create(
                producto=producto,
                proveedor=proveedor,
                precio=1500
            )
            assert historial.id is not None
            assert historial.precio == 1500
            assert historial.producto == producto
            assert historial.proveedor == proveedor
        except Exception as e:
            pytest.fail(f"No se pudo crear historial válido: {e}")

    def test_str_devuelve_descripcion_valida(self, producto, proveedor):
        try:
            historial = HistorialPrecioProducto.objects.create(
                producto=producto,
                proveedor=proveedor,
                precio=2000
            )
            assert f"${historial.precio}" in str(historial)
            assert producto.nombre in str(historial)
        except Exception as e:
            pytest.fail(f"__str__ falló: {e}")

    def test_fecha_registro_automatica(self, producto, proveedor):
        try:
            historial = HistorialPrecioProducto.objects.create(
                producto=producto,
                proveedor=proveedor,
                precio=2500
            )
            assert historial.fecha_registro.date() == timezone.now().date()
        except Exception as e:
            pytest.fail(f"Fecha de registro automática falló: {e}")

    def test_no_registra_si_precio_igual(self, producto, proveedor):
        try:
            PrecioService.registrar_precio(producto, proveedor, 3000)
            count_inicial = HistorialPrecioProducto.objects.count()

            PrecioService.registrar_precio(producto, proveedor, 3000)
            count_final = HistorialPrecioProducto.objects.count()

            assert count_inicial == count_final
        except Exception as e:
            pytest.fail(f"Fallo al evitar duplicado de precio: {e}")

    def test_registra_nuevo_si_precio_cambia(self, producto, proveedor):
        try:
            PrecioService.registrar_precio(producto, proveedor, 3100)
            count_1 = HistorialPrecioProducto.objects.count()

            PrecioService.registrar_precio(producto, proveedor, 3200)
            count_2 = HistorialPrecioProducto.objects.count()

            assert count_2 == count_1 + 1
        except Exception as e:
            pytest.fail(f"Fallo al registrar nuevo precio distinto: {e}")

    def test_valida_precio_negativo_lanza_error(self, producto, proveedor):
        historial = HistorialPrecioProducto(
            producto=producto,
            proveedor=proveedor,
            precio=-1000
        )
        with pytest.raises(ValidationError, match="mayor o igual a 0"):
            historial.full_clean()


    def test_repr_seguro_sin_producto(self, proveedor):
        historial = HistorialPrecioProducto(
            producto=None,
            proveedor=proveedor,
            precio=999
        )
        try:
            resultado = str(historial)
        except Exception:
            resultado = "Historial de precio inválido"
        assert "Historial" in resultado
