from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class NotificationSystem:
    @staticmethod
    def send_critical_notification(subject, message):
        try:
            if settings.DEBUG:
                logger.warning(
                    "Notificación crítica (DEBUG MODE): %s - %s", subject, message
                )
            else:
                send_mail(
                    subject,
                    message,
                    settings.DEFAULT_FROM_EMAIL,
                    settings.ADMINS,
                    fail_silently=False,
                )
        except Exception as e:
            logger.error("Error enviando notificación: %s", str(e))
