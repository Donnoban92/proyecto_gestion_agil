from django.test import TestCase
from django.core.exceptions import ValidationError
from inventario.models import Auditoria, CustomUser
from unittest.mock import patch


class AuditoriaModelTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        try:
            with patch("inventario.models.CustomUser.clean", autospec=True):
                cls.usuario = CustomUser.objects.create_user(
                    username="auditor_test",
                    password="seguro123",
                    first_name="Auditor",
                    last_name="Test",
                    email="auditor@test.cl",
                    rut="12345678-5",
                    telefono="+56912345678",
                    direccion="Calle Falsa 123"
                )
        except Exception as e:
            raise RuntimeError(f"Error al crear el usuario de prueba: {e}")

    def test_auditoria_creacion_valida(self):
        try:
            auditoria = Auditoria.objects.create(
                usuario=self.usuario,
                modelo_afectado="Producto",
                id_objeto=42,
                accion="crear",
                descripcion="Creación de producto de prueba"
            )
            self.assertEqual(auditoria.usuario, self.usuario)
            self.assertEqual(auditoria.modelo_afectado, "Producto")
            self.assertEqual(auditoria.accion, "crear")
            self.assertIn("Producto", str(auditoria))
        except Exception as e:
            self.fail(f"No se pudo crear la auditoría válida: {e}")

    def test_auditoria_accion_invalida_lanza_error(self):
        auditoria = Auditoria(
            usuario=self.usuario,
            modelo_afectado="Proveedor",
            id_objeto=11,
            accion="borrar",  # acción inválida
            descripcion="Intento de acción no válida"
        )
        with self.assertRaises(ValidationError) as context:
            auditoria.full_clean()
        self.assertIn("accion", context.exception.message_dict)

    def test_str_repr_seguro_con_usuario_none(self):
        try:
            auditoria = Auditoria.objects.create(
                usuario=None,
                modelo_afectado="Lote",
                id_objeto=3,
                accion="actualizar",
                descripcion="Actualización de lote sin usuario asignado"
            )
            self.assertIn("actualizar", str(auditoria))
        except Exception as e:
            self.fail(f"No se pudo ejecutar __str__ con usuario=None: {e}")
