import django_filters
from django_filters import rest_framework as filters
from inventario.models import OrdenAutomatica

class OrdenAutomaticaFilter(filters.FilterSet):
    estado = filters.CharFilter(field_name='estado', lookup_expr='iexact')
    proveedor = filters.NumberFilter(field_name='proveedor__id')
    producto = filters.NumberFilter(field_name='producto__id')

    fecha_creacion_min = filters.DateFilter(field_name='fecha_creacion', lookup_expr='gte')
    fecha_creacion_max = filters.DateFilter(field_name='fecha_creacion', lookup_expr='lte')
    fecha_actualizacion_min = filters.DateFilter(field_name='fecha_actualizacion', lookup_expr='gte')
    fecha_actualizacion_max = filters.DateFilter(field_name='fecha_actualizacion', lookup_expr='lte')

    cantidad_min = filters.NumberFilter(field_name='cantidad_ordenada', lookup_expr='gte')
    cantidad_max = filters.NumberFilter(field_name='cantidad_ordenada', lookup_expr='lte')

    producto_nombre = filters.CharFilter(field_name='producto__nombre', lookup_expr='icontains')
    proveedor_nombre = filters.CharFilter(field_name='proveedor__nombre', lookup_expr='icontains')

    class Meta:
        model = OrdenAutomatica
        fields = [
            'estado',
            'proveedor',
            'producto',
            'fecha_creacion_min',
            'fecha_creacion_max',
            'fecha_actualizacion_min',
            'fecha_actualizacion_max',
            'cantidad_min',
            'cantidad_max',
            'producto_nombre',
            'proveedor_nombre',
        ]
