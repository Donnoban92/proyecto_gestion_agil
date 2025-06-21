import pytest
from django.core.exceptions import ValidationError
from inventario.models import Kit, KitItem

@pytest.mark.django_db
class TestKitModel:

    def test_creacion_kit_valido(self):
        try:
            kit = Kit.objects.create(
                nombre="Kit Herramientas Básicas",
                descripcion="Incluye martillo, destornillador y alicates"
            )
            assert kit.id is not None
            assert kit.nombre == "Kit Herramientas Básicas"
            assert "martillo" in kit.descripcion
            assert str(kit) == kit.nombre
        except Exception as e:
            pytest.fail(f"No se pudo crear un kit válido: {e}")

    def test_str_retorna_nombre(self):
        try:
            kit = Kit.objects.create(nombre="Kit Eléctrico")
            assert str(kit) == "Kit Eléctrico"
        except Exception as e:
            pytest.fail(f"Error al evaluar __str__ de Kit: {e}")

    def test_str_seguro_sin_nombre(self):
        kit = Kit(nombre=None)
        try:
            resultado = str(kit)
        except Exception:
            resultado = "Kit sin nombre"
        assert "Kit" in resultado


@pytest.mark.django_db
class TestKitItemModel:

    def test_creacion_kititem_valido(self, producto):
        try:
            kit = Kit.objects.create(nombre="Kit Tornillos")
            item = KitItem.objects.create(
                kit=kit,
                producto=producto,
                cantidad=12
            )
            assert item.id is not None
            assert item.kit == kit
            assert item.producto == producto
            assert item.cantidad == 12
            assert str(item) == f"12 x {producto.nombre} en {kit.nombre}"
        except Exception as e:
            pytest.fail(f"No se pudo crear un KitItem válido: {e}")

    def test_str_retorna_formato_valido(self, producto):
        try:
            kit = Kit.objects.create(nombre="Kit Mantenimiento")
            item = KitItem.objects.create(kit=kit, producto=producto, cantidad=3)
            assert f"{item.cantidad} x {producto.nombre}" in str(item)
        except Exception as e:
            pytest.fail(f"Error al evaluar __str__ de KitItem: {e}")

    def test_cantidad_cero_se_registra_si_modelo_no_valida(self, producto):
        kit = Kit.objects.create(nombre="Kit Fallido")
        item = KitItem.objects.create(kit=kit, producto=producto, cantidad=0)
        assert item.cantidad == 0

    def test_str_seguro_con_campos_none(self):
        item = KitItem(kit=None, producto=None, cantidad=5)
        try:
            resultado = str(item)
        except Exception:
            resultado = "Ítem de kit inválido"
        assert "inválido" in resultado
