from rest_framework.throttling import UserRateThrottle


class VentaRateThrottle(UserRateThrottle):
    scope = "ventas"
