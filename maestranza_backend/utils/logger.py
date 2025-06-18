import logging
from django.core.exceptions import ObjectDoesNotExist
from django.utils.timezone import now

logger = logging.getLogger("audit")

# Mixin reusable para consultar estados de CRUDS
# Aquí se pueden registrar acciones de CRUD


class LoggingMixin:
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip

    def log_action(self, action, object_type, object_id, user, details=None):
        try:
            username = user.username if user else "anonymous"
            user_id = user.id if user else None
            ip_address = (
                self.get_client_ip(self.request)
                if hasattr(self, "request")
                else "unknown"
            )

            log_data = {
                "timestamp": now().isoformat(),
                "action": action.upper(),
                "object_type": object_type,
                "object_id": object_id,
                "user": {"id": user_id, "username": username, "ip": ip_address},
                "details": details,
            }

            if action in ["DELETE", "UPDATE_CRITICAL"]:
                logger.warning("Acción crítica: %s", log_data)
            else:
                logger.info("Acción registrada: %s", log_data)

        except Exception as e:
            logger.error("Error al registrar acción: %s", str(e))
