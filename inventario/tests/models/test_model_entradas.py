from django.test import TestCase
from django.core.exceptions import ValidationError
from inventario.models import (
    EntradaInventario, Producto, Proveedor,
    Categoria, Lote, OrdenAutomatica
)
from maestranza_backend.utils.generar_rut_valido import generar_rut_valido


class EntradaInventarioModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        try:
            cls.categoria = Categoria.objects.create(nombre="Herramientas")
            cls.proveedor = Proveedor.objects.create(
                nombre="ProveeTools",
                rut=generar_rut_valido(),
                correo="contacto@proveetools.cl",
                direccion="Av. Central 789",
                telefono="+56987654321",
                comuna=None
            )
            cls.lote = Lote.objects.create(
                codigo="LT-H001",
                proveedor=cls.proveedor,
                categoria=cls.categoria
            )
            cls.producto = Producto.objects.create(
                nombre="Esmeril Angular",
                descripcion="Esmeril de 7 pulgadas",
                lote=cls.lote,
                precio=48000,
                stock=10,
                stock_minimo=5,
                codigo_barra="11223344",
                sku="ESM-ANG-7"
            )
            cls.orden = OrdenAutomatica.objects.create(
                producto=cls.producto,
                proveedor=cls.proveedor,
                cantidad_ordenada=15,
                estado="pendiente"
            )
        except Exception as e:
            raise RuntimeError(f"Error en setUpTestData: {e}")

    def test_creacion_valida_entrada(self):
        try:
            entrada = EntradaInventario.objects.create(
                producto=self.producto,
                orden=self.orden,
                proveedor=self.proveedor,
                cantidad=15,
                precio_unitario=48000,
                total=720000
            )
            self.assertEqual(entrada.producto, self.producto)
            self.assertEqual(entrada.orden, self.orden)
            self.assertEqual(entrada.proveedor, self.proveedor)
            self.assertEqual(entrada.total, 720000)
        except Exception as e:
            self.fail(f"Fallo al crear entrada válida: {e}")

    def test_creacion_sin_orden_ni_proveedor(self):
        try:
            entrada = EntradaInventario.objects.create(
                producto=self.producto,
                cantidad=5,
                precio_unitario=45000,
                total=225000
            )
            self.assertIsNone(entrada.orden)
            self.assertIsNone(entrada.proveedor)
        except Exception as e:
            self.fail(f"Error inesperado sin orden/proveedor: {e}")

    def test_str_repr_seguro(self):
        try:
            entrada = EntradaInventario.objects.create(
                producto=self.producto,
                cantidad=3,
                precio_unitario=50000,
                total=150000
            )
            self.assertIn("Entrada 3 x Esmeril Angular", str(entrada))
        except Exception as e:
            self.fail(f"Error en __str__: {e}")

    def test_total_calculado_correctamente(self):
        try:
            cantidad = 7
            precio = 47000
            entrada = EntradaInventario.objects.create(
                producto=self.producto,
                cantidad=cantidad,
                precio_unitario=precio,
                total=cantidad * precio
            )
            self.assertEqual(entrada.total, 329000)
        except Exception as e:
            self.fail(f"Fallo en cálculo de total: {e}")

    def test_valida_cantidad_negativa(self):
        entrada = EntradaInventario(
            producto=self.producto,
            cantidad=-2,
            precio_unitario=40000,
            total=-80000
        )
        with self.assertRaises(ValidationError):
            entrada.full_clean()

    def test_valida_precio_unitario_negativo(self):
        entrada = EntradaInventario(
            producto=self.producto,
            cantidad=3,
            precio_unitario=-10000,
            total=-30000
        )
        with self.assertRaises(ValidationError):
            entrada.full_clean()
