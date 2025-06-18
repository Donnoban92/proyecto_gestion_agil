from inventario.models import Notificacion, CustomUser
from django.db.models import Q
import logging

logger = logging.getLogger(__name__)

class NotificacionService:
    @staticmethod
    def crear(usuario, mensaje):
        """Envía una notificación a un usuario."""
        try:
            if usuario and mensaje.strip():
                return Notificacion.objects.create(usuario=usuario, mensaje=mensaje.strip())
            return None
        except Exception as e:
            logger.error(f"Error al crear notificación para usuario {getattr(usuario, 'id', 'N/A')}: {str(e)}")
            return None

    @staticmethod
    def notificar_roles(mensaje, roles):
        """Envía notificación a todos los usuarios de ciertos roles."""
        try:
            if not mensaje.strip():
                return

            usuarios = CustomUser.objects.filter(role__in=roles)
            for usuario in usuarios:
                try:
                    Notificacion.objects.create(usuario=usuario, mensaje=mensaje.strip())
                except Exception as e:
                    logger.error(f"Error al crear notificación para usuario {usuario.id}: {str(e)}")
        except Exception as e:
            logger.error(f"Error al enviar notificaciones por roles {roles}: {str(e)}")
