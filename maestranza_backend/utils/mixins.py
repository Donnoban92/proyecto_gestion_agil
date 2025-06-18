from rest_framework import filters, viewsets, permissions
from django_filters.rest_framework import DjangoFilterBackend
from inventario.models import Proveedor, Producto
from inventario.serializers import ProveedorSerializer, ProductoSerializer
from inventario.permissions import IsInventoryManager


class SearchableMixin:
    filter_backends = [filters.SearchFilter, DjangoFilterBackend]
    search_fields = []


class ProveedorViewSet(SearchableMixin, viewsets.ModelViewSet):
    """
    ViewSet auditable para Proveedor con búsqueda y filtrado.
    """

    queryset = Proveedor.objects.all()
    serializer_class = ProveedorSerializer
    permission_classes = [IsInventoryManager | permissions.IsAdminUser]
    search_fields = ["nombre", "comuna__nombre"]
    filterset_fields = ["comuna", "nombre"]

    def perform_create(self, serializer):
        instance = serializer.save()
        self.log_action(
            "CREATE", "Proveedor", instance.id, self.request.user, serializer.data
        )

    def perform_update(self, serializer):
        instance = serializer.save()
        self.log_action(
            "UPDATE", "Proveedor", instance.id, self.request.user, serializer.data
        )

    def perform_destroy(self, instance):
        object_id = instance.id
        super().perform_destroy(instance)
        self.log_action("DELETE", "Proveedor", object_id, self.request.user)


class ProductoViewSet(SearchableMixin, viewsets.ModelViewSet):
    """
    ViewSet auditable para Producto con búsqueda y filtrado.
    """

    queryset = Producto.objects.all()
    serializer_class = ProductoSerializer
    permission_classes = [IsInventoryManager | permissions.IsAdminUser]
    search_fields = ["nombre", "codigo_barra"]
    filterset_fields = ["id", "categoria", "codigo_barra"]

    def perform_create(self, serializer):
        instance = serializer.save()
        self.log_action(
            "CREATE", "Producto", instance.id, self.request.user, serializer.data
        )

    def perform_update(self, serializer):
        instance = serializer.save()
        self.log_action(
            "UPDATE", "Producto", instance.id, self.request.user, serializer.data
        )

    def perform_destroy(self, instance):
        object_id = instance.id
        super().perform_destroy(instance)
        self.log_action("DELETE", "Producto", object_id, self.request.user)
