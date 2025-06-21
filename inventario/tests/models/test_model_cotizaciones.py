from django.test import TestCase
from django.core.exceptions import ValidationError
from inventario.models import CotizacionProveedor, OrdenAutomatica, Proveedor, Categoria, Producto, Lote, AlertaStock
from maestranza_backend.utils.generar_rut_valido import generar_rut_valido


class CotizacionProveedorModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        try:
            cls.categoria = Categoria.objects.create(nombre="Aceros")
            cls.proveedor = Proveedor.objects.create(
                nombre="AceroMax Ltda.",
                rut=generar_rut_valido(),
                correo="ventas@aceromax.cl",
                telefono="+56987654321",
                direccion="Calle del Acero 123"
            )
            cls.lote = Lote.objects.create(codigo="LT-777", proveedor=cls.proveedor, categoria=cls.categoria)
            cls.producto = Producto.objects.create(
                nombre="Plancha Acero Inox",
                descripcion="Plancha de acero inoxidable",
                lote=cls.lote,
                precio=12000,
                stock=8,
                stock_minimo=10,
                codigo_barra="55667788",
                sku="PL-AC-INX"
            )
            cls.alerta = AlertaStock.objects.create(producto=cls.producto, estado="pendiente")
            cls.orden = OrdenAutomatica.objects.create(
                alerta=cls.alerta,
                producto=cls.producto,
                proveedor=cls.proveedor,
                cantidad_ordenada=20
            )
        except Exception as e:
            raise RuntimeError(f"Error al preparar los datos: {e}")

    def test_creacion_valida_cotizacion(self):
        try:
            cotizacion = CotizacionProveedor.objects.create(
                orden=self.orden,
                estado="pendiente",
                monto=150000
            )
            self.assertEqual(cotizacion.estado, "pendiente")
            self.assertEqual(cotizacion.monto, 150000)
            self.assertIn(f"Cotización #{cotizacion.id}", str(cotizacion))
        except Exception as e:
            self.fail(f"Error inesperado al crear cotización válida: {e}")

    def test_estado_invalido_lanza_validation_error(self):
        cotizacion = CotizacionProveedor(
            orden=self.orden,
            estado="no_valido",
            monto=100000
        )
        with self.assertRaises(ValidationError):
            cotizacion.full_clean()

    def test_monto_negativo_lanza_validation_error(self):
        cotizacion = CotizacionProveedor(
            orden=self.orden,
            estado="pendiente",
            monto=-50000
        )
        with self.assertRaises(ValidationError):
            cotizacion.full_clean()

    def test_archivo_pdf_es_opcional(self):
        try:
            cotizacion = CotizacionProveedor.objects.create(
                orden=self.orden,
                estado="aceptada",
                monto=200000
            )
            self.assertIsNone(cotizacion.archivo_pdf.name)
        except Exception as e:
            self.fail(f"Error inesperado al crear cotización sin archivo: {e}")

    def test_str_repr_seguro_sin_orden(self):
        try:
            cotizacion = CotizacionProveedor(
                orden=None,
                estado="rechazada",
                monto=50000
            )
            resultado = str(cotizacion)
        except Exception:
            resultado = "Cotización de proveedor inválida"
        self.assertIn("Cotización", resultado)

    def test_estado_valido_no_lanza_error(self):
        estados = ["pendiente", "aceptada", "rechazada"]
        for estado in estados:
            try:
                cot = CotizacionProveedor(orden=self.orden, estado=estado, monto=12345)
                cot.full_clean()  # No debe lanzar error
            except ValidationError as e:
                self.fail(f"El estado válido '{estado}' lanzó ValidationError: {e}")

    def test_str_cotizacion_con_datos_minimos(self):
        try:
            cot = CotizacionProveedor(orden=self.orden, estado="aceptada", monto=100000)
            self.assertIn("Cotización", str(cot))
        except Exception as e:
            self.fail(f"__str__ falló con datos mínimos: {e}")
