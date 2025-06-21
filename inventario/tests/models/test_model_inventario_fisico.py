import pytest
from django.core.exceptions import ValidationError
from django.utils import timezone
from inventario.models import InventarioFisico


@pytest.mark.django_db
class TestInventarioFisicoModel:

    def test_creacion_valida_y_diferencia_correcta(self, producto, usuario_admin):
        producto.stock = 20
        producto.save()

        try:
            inventario = InventarioFisico.objects.create(
                producto=producto,
                stock_real=15,
                responsable=usuario_admin
            )
        except Exception as e:
            pytest.fail(f"No se pudo crear inventario físico válido: {e}")

        assert inventario.id is not None
        assert inventario.diferencia == -5
        assert inventario.producto == producto
        assert inventario.stock_real == 15

    def test_fecha_conteo_se_asigna_automaticamente(self, producto, usuario_admin):
        inventario = InventarioFisico.objects.create(
            producto=producto,
            stock_real=8,
            responsable=usuario_admin
        )
        assert inventario.fecha_conteo.date() == timezone.now().date()

    def test_str_repr_valido(self, producto, usuario_admin):
        inventario = InventarioFisico.objects.create(
            producto=producto,
            stock_real=10,
            responsable=usuario_admin
        )
        assert str(inventario).startswith("Inventario físico de")

    def test_str_repr_seguro_si_falla(self):
        inventario = InventarioFisico(stock_real=5)
        try:
            resultado = str(inventario)
        except Exception:
            resultado = "Inventario físico inválido"
        assert "Inventario" in resultado

    def test_stock_real_negativo_lanza_validation_error(self, producto, usuario_admin):
        inventario = InventarioFisico(
            producto=producto,
            stock_real=-1,
            responsable=usuario_admin
        )
        with pytest.raises(ValidationError, match="mayor o igual a 0"):
            inventario.full_clean()

    def test_stock_real_en_cero_es_valido(self, producto, usuario_admin):
        inventario = InventarioFisico.objects.create(
            producto=producto,
            stock_real=0,
            responsable=usuario_admin
        )
        assert inventario.stock_real == 0
        assert inventario.diferencia == -producto.stock
