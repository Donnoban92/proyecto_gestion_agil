import django_filters
from inventario.models import OrdenAutomatica

class OrdenAutomaticaFilter(django_filters.FilterSet):
    estado = django_filters.CharFilter(field_name='estado', lookup_expr='iexact')
    proveedor = django_filters.NumberFilter(field_name='proveedor__id')
    producto = django_filters.NumberFilter(field_name='producto__id')

    class Meta:
        model = OrdenAutomatica
        fields = ['estado', 'proveedor', 'producto']
