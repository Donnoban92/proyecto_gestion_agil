from inventario.models import Auditoria

class AuditoriaService:
    @staticmethod
    def registrar(usuario, modelo, id_objeto, accion, descripcion):
        """Guarda manualmente una entrada de auditoría si se necesita fuera de signals."""
        Auditoria.objects.create(
            usuario=usuario,
            modelo_afectado=modelo,
            id_objeto=id_objeto,
            accion=accion,
            descripcion=descripcion
        )
