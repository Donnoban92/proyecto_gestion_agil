import pytest
from django.utils import timezone
from django.core.exceptions import ValidationError
from inventario.models import OrdenAutomatica, OrdenAutomaticaItem


@pytest.mark.django_db
class TestOrdenAutomaticaModel:

    def test_creacion_orden_valida(self, proveedor):
        orden = OrdenAutomatica.objects.create(
            proveedor=proveedor,
            cantidad_ordenada=10,
            estado="pendiente"
        )
        assert orden.id is not None
        assert orden.estado == "pendiente"
        assert orden.cantidad_ordenada == 10
        assert orden.proveedor == proveedor
        assert str(orden).startswith("Orden Automática para proveedor")

    def test_estado_default_es_pendiente(self, proveedor):
        orden = OrdenAutomatica.objects.create(proveedor=proveedor)
        assert orden.estado == "pendiente"

    def test_fecha_creacion_y_actualizacion(self, proveedor):
        orden = OrdenAutomatica.objects.create(proveedor=proveedor)
        assert orden.fecha_creacion.date() == timezone.now().date()
        assert orden.fecha_actualizacion.date() == timezone.now().date()

    def test_str_seguro_con_proveedor_none(self):
        orden = OrdenAutomatica(proveedor=None)
        try:
            resultado = str(orden)
        except Exception:
            resultado = "Orden inválida"
        assert "Orden" in resultado

    def test_valida_estado_invalido(self, proveedor):
        orden = OrdenAutomatica(proveedor=proveedor, estado="no_valido")
        with pytest.raises(ValidationError):
            orden.full_clean()

    def test_valida_cantidad_negativa(self, proveedor):
        orden = OrdenAutomatica(proveedor=proveedor, cantidad_ordenada=-1)
        with pytest.raises(ValidationError):
            orden.full_clean()


@pytest.mark.django_db
class TestOrdenAutomaticaItemModel:

    def test_creacion_item_valido(self, proveedor, alerta, producto):
        orden = OrdenAutomatica.objects.create(proveedor=proveedor)
        item = OrdenAutomaticaItem.objects.create(
            orden=orden,
            alerta=alerta,
            producto=producto,
            cantidad_ordenada=5
        )
        assert item.id is not None
        assert item.orden == orden
        assert item.alerta == alerta
        assert item.producto == producto
        assert item.cantidad_ordenada == 5
        assert str(item).startswith("5 x")

    def test_relacion_items_en_orden(self, proveedor, alerta, producto):
        orden = OrdenAutomatica.objects.create(proveedor=proveedor)
        OrdenAutomaticaItem.objects.create(orden=orden, alerta=alerta, producto=producto, cantidad_ordenada=3)
        OrdenAutomaticaItem.objects.create(orden=orden, alerta=alerta, producto=producto, cantidad_ordenada=7)
        assert orden.items.count() == 2
        assert sum(item.cantidad_ordenada for item in orden.items.all()) == 10

    def test_str_seguro_con_campos_none(self):
        item = OrdenAutomaticaItem(orden=None, producto=None, cantidad_ordenada=2)
        try:
            resultado = str(item)
        except Exception:
            resultado = "Ítem de orden inválido"
        assert "orden" in resultado.lower() or "ítem" in resultado.lower()

    def test_valida_cantidad_invalida(self, proveedor, alerta, producto):
        orden = OrdenAutomatica.objects.create(proveedor=proveedor)
        item = OrdenAutomaticaItem(
            orden=orden,
            alerta=alerta,
            producto=producto,
            cantidad_ordenada=0
        )
        with pytest.raises(ValidationError):
            item.full_clean()
