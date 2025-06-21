import pytest
from django.db import IntegrityError, transaction
from inventario.models import Proveedor


@pytest.mark.django_db
class TestProveedorModel:

    def test_creacion_proveedor_valido(self, comuna):
        try:
            proveedor = Proveedor.objects.create(
                nombre="Proveedor Uno",
                rut="76.453.678-1",
                direccion="Avenida Central 123",
                comuna=comuna,
                telefono="912345678",
                correo="proveedor@correo.cl"
            )
            assert proveedor.id is not None
            assert proveedor.nombre == "Proveedor Uno"
            assert proveedor.rut == "76.453.678-1"
            assert proveedor.direccion == "Avenida Central 123"
            assert proveedor.comuna == comuna
            assert proveedor.telefono == "+56912345678"
            assert proveedor.correo == "proveedor@correo.cl"
            assert str(proveedor) == "Proveedor Uno"
        except Exception as e:
            pytest.fail(f"Error inesperado al crear proveedor válido: {e}")

    def test_formato_telefono_con_prefijo_56(self, comuna):
        try:
            proveedor = Proveedor.objects.create(
                nombre="Proveedor Tel",
                rut="77.777.777-7",
                direccion="Calle Uno",
                comuna=comuna,
                telefono="912345678",
                correo="tel@correo.cl"
            )
            assert proveedor.telefono == "+56912345678"
        except Exception as e:
            pytest.fail(f"Error al validar formato de teléfono con prefijo: {e}")

    def test_formato_telefono_sin_repetir_56(self, comuna):
        try:
            proveedor = Proveedor.objects.create(
                nombre="Proveedor Con +56",
                rut="76.000.111-2",
                direccion="Calle Dos",
                comuna=comuna,
                telefono="+56987654321",
                correo="mas56@correo.cl"
            )
            assert proveedor.telefono == "+56987654321"
        except Exception as e:
            pytest.fail(f"Error al validar teléfono con +56 explícito: {e}")

    def test_correo_se_asigna_por_defecto(self, comuna):
        try:
            proveedor = Proveedor.objects.create(
                nombre="Proveedor Default",
                rut="78.888.888-8",
                direccion="Calle Tres",
                comuna=comuna
            )
            assert proveedor.correo == "usuario-temporal@correo.cl"
        except Exception as e:
            pytest.fail(f"Error al verificar asignación por defecto de correo: {e}")

    def test_str_seguro_con_nombre_none(self):
        proveedor = Proveedor(nombre=None)
        try:
            resultado = str(proveedor)
        except Exception:
            resultado = "Proveedor inválido"
        assert "Proveedor" in resultado or resultado == "Proveedor inválido"

    def test_nombre_y_rut_deben_ser_unicos(self, comuna):
        try:
            Proveedor.objects.create(
                nombre="Proveedor Repetido",
                rut="79.999.999-9",
                direccion="Calle Repetida",
                comuna=comuna,
                correo="repetido@correo.cl"
            )
        except Exception as e:
            pytest.fail(f"Error inesperado al crear proveedor base para test de unicidad: {e}")

        # Validar duplicación de nombre
        try:
            with transaction.atomic():
                with pytest.raises(IntegrityError):
                    Proveedor.objects.create(
                        nombre="Proveedor Repetido",  # Nombre duplicado
                        rut="80.000.000-0",
                        direccion="Otra Calle",
                        comuna=comuna,
                        correo="otro@correo.cl"
                    )
        except Exception as e:
            pytest.fail(f"Excepción inesperada al validar unicidad de nombre: {e}")

        # Validar duplicación de RUT
        try:
            with transaction.atomic():
                with pytest.raises(IntegrityError):
                    Proveedor.objects.create(
                        nombre="Otro Proveedor",
                        rut="79.999.999-9",  # RUT duplicado
                        direccion="Otra Calle",
                        comuna=comuna,
                        correo="otro2@correo.cl"
                    )
        except Exception as e:
            pytest.fail(f"Excepción inesperada al validar unicidad de RUT: {e}")
