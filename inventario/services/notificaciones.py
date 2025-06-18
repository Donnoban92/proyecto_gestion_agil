from inventario.models import Notificacion, CustomUser
from django.db.models import Q


class NotificacionService:
    @staticmethod
    def crear(usuario, mensaje):
        """Envía una notificación a un usuario."""
        if usuario and mensaje.strip():
            return Notificacion.objects.create(usuario=usuario, mensaje=mensaje.strip())
        return None

    @staticmethod
    def notificar_roles(mensaje, roles):
        """Envía notificación a todos los usuarios de ciertos roles."""
        if not mensaje.strip():
            return

        usuarios = CustomUser.objects.filter(rol__in=roles)
        for usuario in usuarios:
            Notificacion.objects.create(usuario=usuario, mensaje=mensaje.strip())
