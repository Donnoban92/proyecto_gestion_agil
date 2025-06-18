from rest_framework.views import exception_handler as drf_exception_handler
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
import logging

logger = logging.getLogger("audit")


def get_client_ip(request):
    ...


def custom_exception_handler(exc, context):
    # 1) DRF genera un Response para APIException, ValidationError, etc.
    drf_response = drf_exception_handler(exc, context)
    if drf_response is not None:
        # ¡Devuélvelo tal cual! (con {"detail": ...})
        return drf_response

    # 2) Si DRF NO lo manejó: es un error interno → lo formateamos
    request = context.get("request")
    view = context.get("view")
    ip = get_client_ip(request)

    logger.error(
        "Unhandled error - IP: %s | View: %s | Error: %s | Path: %s",
        ip,
        view.__class__.__name__ if view else "UnknownView",
        str(exc),
        getattr(request, "path", ""),
    )

    return Response({"detail": str(exc)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def custom_404_handler(request, exception=None):
    return JsonResponse(
        {
            "error": "Endpoint no encontrado",
            "status_code": status.HTTP_404_NOT_FOUND,
            "path": request.path,
        },
        status=status.HTTP_404_NOT_FOUND,
    )


def custom_500_handler(request):
    return JsonResponse(
        {
            "error": "Error interno del servidor",
            "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
            "request_id": getattr(request, "request_id", None),
        },
        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
    )
