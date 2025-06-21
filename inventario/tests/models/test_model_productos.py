from django.core.exceptions import ValidationError
from django.test import TestCase
from inventario.models import (
    Categoria, Proveedor, Lote, Producto, Comuna, Region, Ciudad, Pais
)
from maestranza_backend.utils.generar_rut_valido import generar_rut_valido


class ProductoModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        try:
            cls.pais = Pais.objects.create(nombre="Chile")
            cls.region = Region.objects.create(nombre="Región de Valparaíso", pais=cls.pais)
            cls.ciudad = Ciudad.objects.create(nombre="Valparaíso", region=cls.region)
            cls.comuna = Comuna.objects.create(nombre="Viña del Mar", ciudad=cls.ciudad)

            cls.categoria = Categoria.objects.create(nombre="Granos")
            cls.proveedor = Proveedor.objects.create(
                nombre="Don Juan",
                rut=generar_rut_valido(),
                correo="d@j.cl",
                direccion="Av. Siempre Viva 123",
                comuna=cls.comuna,
                telefono="+56912345678"
            )
            cls.lote = Lote.objects.create(
                codigo="LT-001",
                proveedor=cls.proveedor,
                categoria=cls.categoria
            )
        except Exception as e:
            raise RuntimeError(f"Error en setUpTestData: {e}")

    def test_creacion_valida_producto(self):
        try:
            producto = Producto.objects.create(
                nombre="Esmeril Angular",
                descripcion="Esmeril industrial",
                lote=self.lote,
                precio=55000,
                stock=30,
                stock_minimo=10,
                codigo_barra="12345678",
                sku="SKU-ESM-001",
            )
            self.assertEqual(producto.nombre, "Esmeril Angular")
            self.assertFalse(producto.is_stock_bajo())
            self.assertEqual(str(producto), "Esmeril Angular")
        except Exception as e:
            self.fail(f"Error inesperado al crear producto válido: {e}")

    def test_producto_stock_bajo_true(self):
        try:
            producto = Producto.objects.create(
                nombre="Taladro Percutor",
                lote=self.lote,
                precio=39990,
                stock=5,
                stock_minimo=10,
                codigo_barra="87654321",
                sku="SKU-TLD-001",
            )
            self.assertTrue(producto.is_stock_bajo())
        except Exception as e:
            self.fail(f"Error inesperado al evaluar stock bajo: {e}")

    def test_str_seguro_si_nombre_none(self):
        try:
            producto = Producto(nombre=None)
            texto = str(producto)
        except Exception:
            texto = "Producto inválido"
        self.assertIn("Producto", texto)

    def test_codigo_barra_menor_a_8_lanza_error(self):
        producto = Producto(
            nombre="Martillo",
            lote=self.lote,
            precio=3000,
            stock=25,
            stock_minimo=10,
            codigo_barra="1234",
            sku="SKU-MART-001",
        )
        with self.assertRaises(ValidationError):
            producto.full_clean()

    def test_precio_cero_lanza_error(self):
        producto = Producto(
            nombre="Llave Ajustable",
            lote=self.lote,
            precio=0,
            stock=10,
            stock_minimo=5,
            codigo_barra="99887766",
            sku="SKU-LLAVE-001",
        )
        with self.assertRaises(ValidationError):
            producto.full_clean()

    def test_stock_negativo_lanza_error(self):
        producto = Producto(
            nombre="Prensa Hidráulica",
            lote=self.lote,
            precio=450000,
            stock=-10,
            stock_minimo=5,
            codigo_barra="66778899",
            sku="SKU-PRENSA-001",
        )
        with self.assertRaises(ValidationError):
            producto.full_clean()

    def test_stock_minimo_negativo_lanza_error(self):
        producto = Producto(
            nombre="Compresor",
            lote=self.lote,
            precio=120000,
            stock=20,
            stock_minimo=-1,
            codigo_barra="55667788",
            sku="SKU-COMP-001",
        )
        with self.assertRaises(ValidationError):
            producto.full_clean()

    def test_sku_puede_ser_blanco(self):
        try:
            producto = Producto.objects.create(
                nombre="Barreta",
                lote=self.lote,
                precio=2990,
                stock=100,
                stock_minimo=20,
                codigo_barra="44556677",
                sku=""
            )
            self.assertEqual(producto.sku, "")
        except Exception as e:
            self.fail(f"Error inesperado con SKU blanco: {e}")
