from django.test import TestCase
from django.core.exceptions import ValidationError
from inventario.models import Categoria, Proveedor, Lote, Producto, AlertaStock
from maestranza_backend.utils.generar_rut_valido import generar_rut_valido
from datetime import datetime


class AlertaStockModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        try:
            cls.categoria = Categoria.objects.create(nombre="Eléctrica")
            cls.proveedor = Proveedor.objects.create(
                nombre="Cable Ltda",
                rut=generar_rut_valido(),
                correo="contacto@cable.cl",
                telefono="56999998888",
                direccion="Ruta 5 Norte KM 45"
            )
            cls.lote = Lote.objects.create(
                codigo="LT-001",
                proveedor=cls.proveedor,
                categoria=cls.categoria
            )
            cls.producto = Producto.objects.create(
                nombre="Cobre 1kg",
                descripcion="Rollos de cobre",
                lote=cls.lote,
                precio=9500,
                stock=3,
                stock_minimo=5,
                codigo_barra="22334455",
                sku="CBR-001"
            )
        except Exception as e:
            raise RuntimeError(f"Error al preparar los datos de prueba: {e}")

    def test_alerta_creacion_valida(self):
        try:
            alerta = AlertaStock.objects.create(
                producto=self.producto,
                estado="pendiente"
            )
            self.assertEqual(alerta.estado, "pendiente")
            self.assertEqual(alerta.producto, self.producto)
            self.assertEqual(str(alerta), f"Alerta de stock: {self.producto.nombre} - Estado: pendiente")
        except Exception as e:
            self.fail(f"No se pudo crear una alerta válida: {e}")

    def test_alerta_estado_invalido_lanza_validation_error(self):
        alerta = AlertaStock(producto=self.producto, estado="no_valido")
        with self.assertRaises(ValidationError):
            alerta.full_clean()

    def test_alerta_str_muestra_estado(self):
        try:
            alerta = AlertaStock.objects.create(producto=self.producto, estado="resuelta")
            self.assertIn("resuelta", str(alerta))
        except Exception as e:
            self.fail(f"No se pudo evaluar el método __str__: {e}")

    def test_fecha_silencio_por_default_none(self):
        try:
            alerta = AlertaStock.objects.create(producto=self.producto, estado="pendiente")
            self.assertIsNone(alerta.fecha_silencio)
        except Exception as e:
            self.fail(f"No se pudo validar fecha_silencio por defecto: {e}")

    def test_alerta_productos_nulos_falla(self):
        with self.assertRaises(ValidationError):
            alerta = AlertaStock(estado="pendiente")
            alerta.full_clean()

    def test_estados_validos_permitidos(self):
        estados_validos = ["activa", "pendiente", "archivada", "silenciada", "inactiva"]
        for estado in estados_validos:
            try:
                alerta = AlertaStock(producto=self.producto, estado=estado)
                alerta.full_clean()  # No debe lanzar error
            except ValidationError as ve:
                self.fail(f"El estado válido '{estado}' generó ValidationError: {ve}")
            except Exception as e:
                self.fail(f"El estado válido '{estado}' lanzó excepción inesperada: {e}")

    def test_fecha_creacion_y_actualizacion_se_asignan(self):
        try:
            alerta = AlertaStock.objects.create(producto=self.producto, estado="pendiente")
            self.assertIsNotNone(alerta.fecha_creacion)
            self.assertIsNotNone(alerta.fecha_actualizacion)
            self.assertIsInstance(alerta.fecha_creacion, datetime)
            self.assertIsInstance(alerta.fecha_actualizacion, datetime)
        except Exception as e:
            self.fail(f"No se asignaron fechas correctamente: {e}")
