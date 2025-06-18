from rest_framework import permissions
from inventario.models import CustomUser  # ajusta si tu modelo está en otra app
from rest_framework.permissions import BasePermission

# Permite solo a administradores
class IsAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == CustomUser.Roles.ADMIN

# Permite a administradores o gestores de inventario
class IsInventoryManager(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role in [
            CustomUser.Roles.ADMIN,
            CustomUser.Roles.INVENTARIO
        ]

class IsInventoryManagerOrAdmin(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and (
            request.user.rol in ['admin', 'inventario']
        )

class IsAdminUserOnly(BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.rol == 'admin'

# Permite solo a compradores
class IsComprador(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == CustomUser.Roles.COMPRADOR

# Permite solo a encargados de logística
class IsLogistica(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == CustomUser.Roles.LOGISTICA

# Permite solo a jefes de producción
class IsJefeProduccion(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == CustomUser.Roles.PRODUCCION

# Permite solo a auditores
class IsAuditor(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == CustomUser.Roles.AUDITOR

# Permite solo a gerentes de proyectos
class IsGerenteProyectos(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == CustomUser.Roles.PROYECTOS

# Permite solo a trabajadores de planta
class IsPlanta(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.user.is_authenticated and request.user.role == CustomUser.Roles.PLANTA
