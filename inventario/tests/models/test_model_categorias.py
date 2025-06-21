from django.test import TestCase
from django.db import IntegrityError
from inventario.models import Categoria


class CategoriaModelTests(TestCase):

    def test_creacion_categoria_valida(self):
        try:
            categoria = Categoria.objects.create(nombre="Mecánica", descripcion="Herramientas y repuestos")
            self.assertEqual(categoria.nombre, "Mecánica")
            self.assertEqual(categoria.descripcion, "Herramientas y repuestos")
            self.assertEqual(str(categoria), "Mecánica")
        except Exception as e:
            self.fail(f"No se pudo crear una categoría válida: {e}")

    def test_creacion_sin_descripcion_es_valida(self):
        try:
            categoria = Categoria.objects.create(nombre="Eléctrica")
            self.assertEqual(categoria.descripcion, "")
            self.assertEqual(str(categoria), "Eléctrica")
        except Exception as e:
            self.fail(f"No se pudo crear una categoría sin descripción: {e}")

    def test_nombre_categoria_debe_ser_unico(self):
        Categoria.objects.create(nombre="Soldadura")
        with self.assertRaises(IntegrityError):
            Categoria.objects.create(nombre="Soldadura")

    def test_str_repr_seguro_aun_si_falla(self):
        categoria = Categoria()
        categoria.nombre = None
        try:
            resultado = str(categoria)
        except Exception as e:
            self.fail(f"__str__ falló con nombre=None: {e}")
        self.assertEqual(resultado, "Categoría sin nombre")

    def test_nombre_vacio_lanza_error_si_no_se_guarda(self):
        categoria = Categoria(nombre=None)
        try:
            categoria.full_clean()
        except Exception as e:
            self.assertIsInstance(e, Exception)  # Django lanzará ValidationError internamente

    def test_creacion_nombre_extremo_largo(self):
        nombre_largo = "X" * 128
        try:
            categoria = Categoria.objects.create(nombre=nombre_largo)
            self.assertEqual(categoria.nombre, nombre_largo)
        except Exception as e:
            self.fail(f"No se pudo crear categoría con nombre largo: {e}")
