from inventario.models import Auditoria
import logging

logger = logging.getLogger(__name__)

class AuditoriaService:
    @staticmethod
    def registrar(usuario, modelo, id_objeto, accion, descripcion):
        """Guarda manualmente una entrada de auditoría si se necesita fuera de signals."""
        try:
            Auditoria.objects.create(
                usuario=usuario,
                modelo_afectado=modelo,
                id_objeto=id_objeto,
                accion=accion,
                descripcion=descripcion
            )
        except Exception as e:
            logger.error(f"Error al registrar auditoría para {modelo} id {id_objeto}: {str(e)}")
