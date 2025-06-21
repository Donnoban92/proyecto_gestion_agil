from django.test import TestCase
from inventario.models import (
    SalidaInventario, Producto, Proveedor, Categoria,
    Lote, CustomUser, Cargo
)
from maestranza_backend.utils.generar_rut_valido import generar_rut_valido
from maestranza_backend.utils.validar_rut import validar_rut
from django.core.exceptions import ValidationError


def formatear_rut(rut_raw: str) -> str:
    cuerpo, dv = rut_raw.split("-")
    cuerpo_formateado = f"{int(cuerpo):,}".replace(",", ".")
    return f"{cuerpo_formateado}-{dv}"


class SalidaInventarioModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        try:
            cls.cargo = Cargo.objects.create(nombre="Técnico")
            cls.categoria = Categoria.objects.create(nombre="Eléctrica")

            def rut_valido_formateado():
                for _ in range(10):
                    rut = formatear_rut(generar_rut_valido())
                    if validar_rut(rut):
                        return rut
                raise ValueError("No se pudo generar un RUT válido después de 10 intentos")

            cls.proveedor = Proveedor.objects.create(
                nombre="Suministros Eléctricos",
                rut=rut_valido_formateado(),
                correo="contacto@electrosum.cl",
                direccion="Av. Voltaje 123",
                telefono="+56977778888",
                comuna=None
            )

            cls.lote = Lote.objects.create(
                codigo="LT-EL001",
                proveedor=cls.proveedor,
                categoria=cls.categoria
            )

            cls.producto = Producto.objects.create(
                nombre="Cinta Aisladora",
                descripcion="Rollo de 20m",
                lote=cls.lote,
                precio=1500,
                stock=50,
                stock_minimo=10,
                codigo_barra="55667788",
                sku="CINTA-ISL"
            )

            cls.responsable = CustomUser.objects.create_user(
                username="usuario_salida",
                password="salida123",
                first_name="Usuario",
                last_name="Salida",
                email="salida@test.cl",
                rut=rut_valido_formateado(),
                telefono="+56911223344",
                direccion="Calle Salida 456",
                cargo=cls.cargo,
                comuna=None
            )
        except Exception as e:
            raise Exception(f"Error en setUpTestData: {e}")

    def test_creacion_valida_salida(self):
        try:
            salida = SalidaInventario.objects.create(
                producto=self.producto,
                responsable=self.responsable,
                cantidad=10,
                motivo="consumo",
                observacion="Entrega a personal técnico"
            )
            self.assertEqual(salida.producto, self.producto)
            self.assertEqual(salida.responsable, self.responsable)
            self.assertEqual(salida.cantidad, 10)
            self.assertEqual(salida.motivo, "consumo")
            self.assertEqual(salida.observacion, "Entrega a personal técnico")
        except Exception as e:
            self.fail(f"Fallo al crear salida válida: {e}")

    def test_salida_sin_responsable(self):
        try:
            salida = SalidaInventario.objects.create(
                producto=self.producto,
                cantidad=5,
                motivo="ajuste",
                observacion="Ajuste por error de inventario"
            )
            self.assertIsNone(salida.responsable)
        except Exception as e:
            self.fail(f"Fallo al crear salida sin responsable: {e}")

    def test_str_repr_seguro(self):
        try:
            salida = SalidaInventario.objects.create(
                producto=self.producto,
                cantidad=7,
                motivo="merma",
                observacion="Producto dañado"
            )
            self.assertIn("Salida 7 x Cinta Aisladora", str(salida))
        except Exception as e:
            self.fail(f"Error inesperado en __str__: {e}")

    def test_creacion_sin_observacion(self):
        try:
            salida = SalidaInventario.objects.create(
                producto=self.producto,
                responsable=self.responsable,
                cantidad=3,
                motivo="reubicacion"
            )
            self.assertEqual(salida.observacion, "")
        except Exception as e:
            self.fail(f"Fallo al crear salida sin observación: {e}")

    def test_cantidad_cero_invalida(self):
        try:
            salida = SalidaInventario(
                producto=self.producto,
                responsable=self.responsable,
                cantidad=0,
                motivo="error"
            )
            with self.assertRaises(ValidationError):
                salida.full_clean()
        except Exception as e:
            self.fail(f"Error inesperado al validar cantidad cero: {e}")

    def test_motivo_requerido(self):
        try:
            salida = SalidaInventario(
                producto=self.producto,
                responsable=self.responsable,
                cantidad=5,
                motivo=None
            )
            with self.assertRaises(ValidationError):
                salida.full_clean()
        except Exception as e:
            self.fail(f"Error inesperado al validar motivo requerido: {e}")
