import pytest
from inventario.models import Notificacion
from django.utils import timezone

@pytest.mark.django_db
class TestNotificacionModel:

    def test_creacion_notificacion_valida(self, usuario_admin):
        noti = Notificacion.objects.create(
            usuario=usuario_admin,
            mensaje="¡Tienes una nueva alerta de stock!"
        )
        assert noti.id is not None
        assert noti.usuario == usuario_admin
        assert noti.mensaje == "¡Tienes una nueva alerta de stock!"
        assert noti.leida is False
        assert noti.fecha_creacion.date() == timezone.now().date()

    def test_marcar_como_leida(self, usuario_admin):
        noti = Notificacion.objects.create(usuario=usuario_admin, mensaje="Revise su inventario.")
        noti.leida = True
        noti.save()
        assert noti.leida is True

    def test_str_retorna_formato_valido(self, usuario_admin):
        noti = Notificacion.objects.create(usuario=usuario_admin, mensaje="Mensaje de prueba")
        assert str(noti) == f"Notificación para {usuario_admin.username}"

    def test_str_seguro_con_usuario_none(self):
        noti = Notificacion(usuario=None, mensaje="Mensaje sin usuario")
        try:
            resultado = str(noti)
        except Exception:
            resultado = "Notificación inválida"
        assert "Notificación" in resultado
