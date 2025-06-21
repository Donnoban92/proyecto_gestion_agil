from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status,viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from inventario.filters import OrdenAutomaticaFilter
from maestranza_backend.utils.generar_rut_valido import generar_rut_valido
from drf_spectacular.utils import extend_schema, extend_schema_view
from rest_framework.permissions import IsAuthenticated
from maestranza_backend.permissions import (
    IsAdmin, IsInventoryManager, IsInventoryManagerOrAdmin, IsAdminUserOnly
    )
from .models import (
    Pais, Region, Ciudad, Comuna, Cargo, CustomUser,
    Categoria, Proveedor, Lote, Producto, AlertaStock, 
    OrdenAutomatica, OrdenAutomaticaItem, EntradaInventario,
    SalidaInventario, CotizacionProveedor, HistorialPrecioProducto,
    Kit, KitItem, Auditoria, Notificacion, InventarioFisico
    )
from .serializers import(
    PaisSerializer, RegionSerializer, CiudadSerializer, ComunaSerializer, CargoSerializer, CustomUserSerializer,
    CategoriaSerializer, ProductoSerializer, LoteSerializer, ProveedorSerializer, AlertaStockSerializer,
    OrdenAutomaticaSerializer, OrdenAutomaticaItemSerializer, EntradaInventarioSerializer,
    SalidaInventarioSerializer, CotizacionProveedorSerializer, HistorialPrecioProductoSerializer,
    KitSerializer, KitItemSerializer, AuditoriaSerializer, NotificacionSerializer, InventarioFisicoSerializer
)
import logging
logger = logging.getLogger("django.request")

# -----------------------------------------------#
# Creación de los viewsets localizacion regional.
# -----------------------------------------------#

# Create your views here.
@extend_schema_view(
    list=extend_schema(summary="Listar todos los países"),
    retrieve=extend_schema(summary="Obtener detalle de un país"),
    create=extend_schema(summary="Crear un nuevo país"),
    update=extend_schema(summary="Actualizar un país existente"),
    partial_update=extend_schema(summary="Actualizar parcialmente un país"),
    destroy=extend_schema(summary="Eliminar un país"),
)
class PaisViewSet(viewsets.ModelViewSet):
    queryset = Pais.objects.all().order_by('nombre')
    serializer_class = PaisSerializer

@extend_schema_view(
    list=extend_schema(summary="Listar regiones"),
    retrieve=extend_schema(summary="Detalle de una región"),
    create=extend_schema(summary="Crear una región"),
    update=extend_schema(summary="Actualizar una región"),
    partial_update=extend_schema(summary="Actualizar parcialmente una región"),
    destroy=extend_schema(summary="Eliminar una región"),
)
class RegionViewSet(viewsets.ModelViewSet):
    queryset = Region.objects.select_related('pais').order_by('nombre')
    serializer_class = RegionSerializer

@extend_schema_view(
    list=extend_schema(summary="Listar ciudades"),
    retrieve=extend_schema(summary="Detalle de una ciudad"),
    create=extend_schema(summary="Crear una ciudad"),
    update=extend_schema(summary="Actualizar una ciudad"),
    partial_update=extend_schema(summary="Actualizar parcialmente una ciudad"),
    destroy=extend_schema(summary="Eliminar una ciudad"),
)
class CiudadViewSet(viewsets.ModelViewSet):
    queryset = Ciudad.objects.select_related('region__pais').order_by('nombre')
    serializer_class = CiudadSerializer

@extend_schema_view(
    list=extend_schema(summary="Listar comunas"),
    retrieve=extend_schema(summary="Detalle de una comuna"),
    create=extend_schema(summary="Crear una comuna"),
    update=extend_schema(summary="Actualizar una comuna"),
    partial_update=extend_schema(summary="Actualizar parcialmente una comuna"),
    destroy=extend_schema(summary="Eliminar una comuna"),
)
class ComunaViewSet(viewsets.ModelViewSet):
    queryset = Comuna.objects.select_related('ciudad__region').order_by('nombre')
    serializer_class = ComunaSerializer

@extend_schema_view(
    list=extend_schema(summary="Listar cargos"),
    retrieve=extend_schema(summary="Detalle de un cargo"),
    create=extend_schema(summary="Crear un cargo"),
    update=extend_schema(summary="Actualizar un cargo"),
    partial_update=extend_schema(summary="Actualizar parcialmente un cargo"),
    destroy=extend_schema(summary="Eliminar un cargo"),
)
class CargoViewSet(viewsets.ModelViewSet):
    queryset = Cargo.objects.all().order_by('nombre')
    serializer_class = CargoSerializer

# --------------------------------------------------------#
# Creación de los viewsets fundamentales para el proyecto.
# --------------------------------------------------------#

# Creacion del viewset de CUSTOMUSER
@extend_schema_view(
    list=extend_schema(
        summary="Listar usuarios registrados",
        description="Devuelve una lista paginada de usuarios con filtros por rol, comuna y estado.",
        tags=["Usuarios"]
    ),
    retrieve=extend_schema(
        summary="Obtener detalle de un usuario",
        description="Muestra los campos completos de un usuario individual, incluyendo comuna y cargo.",
        tags=["Usuarios"]
    ),
    create=extend_schema(
        summary="Crear un nuevo usuario",
        description="Registra un nuevo usuario validando correo, RUT, teléfono y rol asignado.",
        tags=["Usuarios"]
    ),
    update=extend_schema(
        summary="Actualizar un usuario",
        description="Permite actualizar datos del usuario, excepto el correo una vez registrado.",
        tags=["Usuarios"]
    ),
    partial_update=extend_schema(
        summary="Actualizar parcialmente un usuario",
        description="Modifica parcialmente los datos del usuario (no permite cambiar el correo).",
        tags=["Usuarios"]
    ),
    destroy=extend_schema(
        summary="Eliminar usuario",
        description="Elimina lógicamente o físicamente un usuario del sistema según permisos.",
        tags=["Usuarios"]
    ),
)
class CustomUserViewSet(viewsets.ModelViewSet):
    """
    ViewSet profesional para la gestión de usuarios en Maestranzas Unidos S.A.
    Incluye control de permisos, validación de roles y seguridad sobre campos clave.
    """
    queryset = CustomUser.objects.select_related('comuna__ciudad__region__pais', 'cargo').all()
    serializer_class = CustomUserSerializer
    permission_classes = [permissions.IsAuthenticated]  # Se puede personalizar por rol
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['role', 'is_active', 'comuna', 'cargo']
    search_fields = ['username', 'first_name', 'last_name', 'rut', 'correo']
    ordering_fields = ['username', 'first_name', 'last_name', 'date_joined']
    ordering = ['-date_joined']

    def perform_create(self, serializer):
        # Forzar lower case en correo y proteger correo duplicado en capa de vista
        validated_data = serializer.validated_data
        correo = validated_data.get("correo")
        if correo:
            validated_data["correo"] = correo.lower()
        serializer.save()

    def perform_update(self, serializer):
        # Evitamos que se modifique el correo si ya existe
        instance = self.get_object()
        validated_data = serializer.validated_data
        correo = validated_data.get("correo", instance.correo)

        if instance.correo != correo:
            raise serializers.ValidationError("El correo no puede ser modificado una vez registrado.")

        serializer.save()

# Creacion del viewset CATEGORIA
@extend_schema_view(
    list=extend_schema(
        summary="Listar categorías",
        description="Devuelve una lista de todas las categorías registradas en el sistema.",
        tags=["Categorías"]
    ),
    retrieve=extend_schema(
        summary="Obtener detalle de una categoría",
        description="Retorna los detalles de una categoría específica por su ID.",
        tags=["Categorías"]
    ),
    create=extend_schema(
        summary="Crear una nueva categoría",
        description="Permite registrar una nueva categoría validando nombre único y descripción opcional.",
        tags=["Categorías"]
    ),
    update=extend_schema(
        summary="Actualizar categoría",
        description="Permite modificar todos los campos de una categoría existente.",
        tags=["Categorías"]
    ),
    partial_update=extend_schema(
        summary="Actualizar parcialmente categoría",
        description="Permite modificar parcialmente los campos de una categoría (por ejemplo, solo la descripción).",
        tags=["Categorías"]
    ),
    destroy=extend_schema(
        summary="Eliminar categoría",
        description="Elimina una categoría solo si no está asociada a productos.",
        tags=["Categorías"]
    ),
)
class CategoriaViewSet(viewsets.ModelViewSet):
    queryset = Categoria.objects.all().order_by('nombre')
    serializer_class = CategoriaSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['nombre', 'descripcion']
    ordering_fields = ['nombre', 'id']
    ordering = ['nombre']

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            if instance.producto_set.exists():
                raise serializers.ValidationError({
                    "error": "No se puede eliminar la categoría porque está asociada a productos."
                })
            return super().destroy(request, *args, **kwargs)
        except Exception as e:
            raise serializers.ValidationError({"error": f"No se pudo eliminar la categoría: {str(e)}"})

# Creacion del viewset PROVEEDOR
@extend_schema_view(
    list=extend_schema(
        summary="Listar proveedores",
        description="Devuelve una lista completa de proveedores registrados. Se puede filtrar por comuna y buscar por nombre, RUT o correo.",
        tags=["Proveedores"]
    ),
    retrieve=extend_schema(
        summary="Obtener detalle de un proveedor",
        description="Retorna la información detallada de un proveedor específico, incluyendo comuna y contacto.",
        tags=["Proveedores"]
    ),
    create=extend_schema(
        summary="Registrar un nuevo proveedor",
        description="Crea un nuevo proveedor validando nombre, RUT, correo y teléfono. No se permiten duplicados.",
        tags=["Proveedores"]
    ),
    update=extend_schema(
        summary="Actualizar proveedor",
        description="Actualiza todos los datos de un proveedor. Asegura que el correo y RUT sigan siendo únicos.",
        tags=["Proveedores"]
    ),
    partial_update=extend_schema(
        summary="Actualizar parcialmente proveedor",
        description="Permite actualizar uno o más campos del proveedor sin modificar todo el registro.",
        tags=["Proveedores"]
    ),
    destroy=extend_schema(
        summary="Eliminar proveedor",
        description="Elimina un proveedor solo si no está asociado a productos, lotes o entradas de inventario.",
        tags=["Proveedores"]
    ),
)
class ProveedorViewSet(viewsets.ModelViewSet):
    queryset = Proveedor.objects.all().order_by('id')
    serializer_class = ProveedorSerializer
    lookup_field = "id"
    filterset_fields = ['comuna']
    search_fields = ['nombre', 'rut', 'correo']
    ordering_fields = ['id', 'nombre', 'rut']
    ordering = ['id']
    permission_classes = [permissions.IsAuthenticated]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            if (
                instance.lotes.exists() or
                EntradaInventario.objects.filter(proveedor=instance).exists() or
                Producto.objects.filter(lote__proveedor=instance).exists()
            ):
                raise serializers.ValidationError({
                    "error": "No se puede eliminar el proveedor porque está asociado a productos, lotes o entradas."
                })
            return super().destroy(request, *args, **kwargs)
        except Exception as e:
            raise serializers.ValidationError({"error": f"No se pudo eliminar el proveedor: {str(e)}"})

# Creacion del viewset LOTE
@extend_schema_view(
    list=extend_schema(
        summary="Listar lotes",
        description="Devuelve un listado de todos los lotes registrados, con posibilidad de filtrar por proveedor, categoría y fechas.",
        tags=["Lotes"]
    ),
    retrieve=extend_schema(
        summary="Obtener detalle de un lote",
        description="Muestra la información detallada de un lote específico, incluyendo proveedor, categoría y fechas.",
        tags=["Lotes"]
    ),
    create=extend_schema(
        summary="Crear un nuevo lote",
        description="Permite registrar un nuevo lote validando código único, proveedor, categoría y fechas coherentes.",
        tags=["Lotes"]
    ),
    update=extend_schema(
        summary="Actualizar lote",
        description="Actualiza completamente los datos de un lote, excepto su código.",
        tags=["Lotes"]
    ),
    partial_update=extend_schema(
        summary="Actualizar parcialmente un lote",
        description="Permite modificar algunos campos del lote sin afectar el resto. El código no es editable.",
        tags=["Lotes"]
    ),
    destroy=extend_schema(
        summary="Eliminar lote",
        description="Elimina un lote si no tiene productos asociados. Operación protegida por validación.",
        tags=["Lotes"]
    ),
)
class LoteViewSet(viewsets.ModelViewSet):
    queryset = Lote.objects.select_related("proveedor", "categoria").all().order_by("-fecha_fabricacion")
    serializer_class = LoteSerializer
    lookup_field = "id"
    filterset_fields = ["proveedor", "categoria", "fecha_fabricacion", "fecha_vencimiento"]
    search_fields = ["codigo", "observaciones", "proveedor__nombre", "categoria__nombre"]
    ordering_fields = ["fecha_fabricacion", "fecha_vencimiento", "codigo"]
    ordering = ["-fecha_fabricacion"]
    permission_classes = [permissions.IsAuthenticated]

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        try:
            if Producto.objects.filter(lote=instance).exists():
                raise serializers.ValidationError({
                    "error": "No se puede eliminar el lote porque hay productos asociados."
                })
            return super().destroy(request, *args, **kwargs)
        except Exception as e:
            raise serializers.ValidationError({"error": f"No se pudo eliminar el lote: {str(e)}"})

# Creacion del viewset PRODUCTO
@extend_schema_view(
    list=extend_schema(
        summary="Listar productos",
        description="Devuelve un listado de todos los productos registrados, incluyendo lote, proveedor, categoría y estado de stock.",
        tags=["Productos"]
    ),
    retrieve=extend_schema(
        summary="Obtener detalle de un producto",
        description="Muestra la información detallada de un producto específico, incluyendo su stock y relaciones.",
        tags=["Productos"]
    ),
    create=extend_schema(
        summary="Crear un nuevo producto",
        description="Registra un producto validando lote, stock mínimo, código de barras, SKU y precio.",
        tags=["Productos"]
    ),
    update=extend_schema(
        summary="Actualizar producto",
        description="Permite modificar todos los datos de un producto, excepto el SKU.",
        tags=["Productos"]
    ),
    partial_update=extend_schema(
        summary="Actualizar parcialmente producto",
        description="Permite editar uno o más campos del producto sin afectar el resto. El SKU no es editable.",
        tags=["Productos"]
    ),
    destroy=extend_schema(
        summary="Eliminar producto",
        description="Elimina un producto solo si no tiene stock disponible. Operación validada automáticamente.",
        tags=["Productos"]
    ),
)
class ProductoViewSet(viewsets.ModelViewSet):
    """
    ViewSet profesional para la gestión de productos en Maestranzas Unidos S.A.
    Incluye lógica de stock mínimo, protección de SKU y seguridad en borrado.
    """
    queryset = Producto.objects.select_related('lote__proveedor', 'lote__categoria').all()
    serializer_class = ProductoSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['lote', 'habilitado', 'stock']
    search_fields = ['nombre', 'codigo_barra', 'sku', 'lote__codigo']
    ordering_fields = ['nombre', 'precio', 'stock', 'fecha_actualizacion']
    ordering = ['id']

    def destroy(self, request, *args, **kwargs):
        try:
            instance = self.get_object()
            if instance.stock > 0:
                raise ValidationError({"error": "No se puede eliminar un producto con stock disponible."})
            return super().destroy(request, *args, **kwargs)
        except Producto.DoesNotExist:
            return Response({"detail": "Producto no encontrado."}, status=status.HTTP_404_NOT_FOUND)
        except ValidationError as ve:
            return Response(ve.detail, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            return Response({"error": f"Error inesperado al eliminar producto: {str(e)}"},
                            status=status.HTTP_500_INTERNAL_SERVER_ERROR)

# Creación del viewset ALERTASTOCK
@extend_schema_view(
    list=extend_schema(
        summary="Listar alertas de stock",
        description="Devuelve un listado de alertas activas, pendientes o archivadas asociadas a productos con bajo stock.",
        tags=["Alertas de Stock"]
    ),
    retrieve=extend_schema(
        summary="Obtener detalle de una alerta",
        description="Muestra la información completa de una alerta, incluyendo producto, proveedor, estado y fechas.",
        tags=["Alertas de Stock"]
    ),
    create=extend_schema(
        summary="Crear alerta de stock",
        description="Crea una nueva alerta si el producto tiene stock bajo. Valida que no exista ya una alerta activa.",
        tags=["Alertas de Stock"]
    ),
    update=extend_schema(
        summary="Actualizar alerta de stock",
        description="Permite modificar el estado o asociar una orden relacionada a la alerta.",
        tags=["Alertas de Stock"]
    ),
    partial_update=extend_schema(
        summary="Actualizar parcialmente una alerta",
        description="Modifica campos específicos de una alerta como su estado o fecha de silencio.",
        tags=["Alertas de Stock"]
    ),
    destroy=extend_schema(
        summary="Eliminar alerta",
        description="Elimina una alerta solo si no está usada ni archivada o silenciada.",
        tags=["Alertas de Stock"]
    ),
)
class AlertaStockViewSet(viewsets.ModelViewSet):
    """
    ViewSet para la gestión de alertas de stock.
    Solo accesible por usuarios autenticados, preferentemente administradores o gestores de inventario.
    """
    queryset = AlertaStock.objects.select_related("producto__lote__proveedor", "producto__lote__categoria").all()
    serializer_class = AlertaStockSerializer
    permission_classes = [permissions.IsAuthenticated, IsInventoryManager]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['estado', 'producto', 'usada_para_orden']
    search_fields = ['producto__nombre', 'producto__sku', 'producto__lote__proveedor__nombre']
    ordering_fields = ['fecha_creacion', 'estado']
    ordering = ['-fecha_creacion']

    def destroy(self, request, *args, **kwargs):
        alerta = self.get_object()
        try:
            if alerta.estado in ['archivada', 'silenciada'] or alerta.usada_para_orden:
                return Response(
                    {"error": "No se puede eliminar una alerta que ya fue procesada o archivada."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            return super().destroy(request, *args, **kwargs)
        except Exception as e:
            return Response(
                {"error": f"Ocurrió un error al intentar eliminar la alerta: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

# Creación del viewset ORDENAUTOMATICA
@extend_schema_view(
    list=extend_schema(
        summary="Listar órdenes automáticas",
        description="Devuelve todas las órdenes generadas por alertas de stock, incluyendo su estado, proveedor y producto asociado.",
        tags=["Órdenes Automáticas"]
    ),
    retrieve=extend_schema(
        summary="Obtener detalle de una orden automática",
        description="Muestra la información detallada de una orden específica, incluyendo producto, proveedor y estado.",
        tags=["Órdenes Automáticas"]
    ),
    create=extend_schema(
        summary="Crear orden automática",
        description="Permite crear una orden a partir de una alerta activa o pendiente. Valida que no haya sido usada.",
        tags=["Órdenes Automáticas"]
    ),
    update=extend_schema(
        summary="Actualizar orden automática",
        description="Permite modificar completamente una orden en estado pendiente. No puede usarse si está completada.",
        tags=["Órdenes Automáticas"]
    ),
    partial_update=extend_schema(
        summary="Actualizar parcialmente una orden automática",
        description="Modifica campos específicos de una orden si esta aún no ha sido usada ni completada.",
        tags=["Órdenes Automáticas"]
    ),
    destroy=extend_schema(
        summary="Eliminar orden automática",
        description="Marca una orden como 'eliminada' si no ha sido completada ni utilizada para ingreso de inventario.",
        tags=["Órdenes Automáticas"]
    ),
)
class OrdenAutomaticaViewSet(viewsets.ModelViewSet):
    queryset = OrdenAutomatica.objects.select_related(
        'proveedor', 'producto', 'alerta'
    ).prefetch_related('items').all()
    serializer_class = OrdenAutomaticaSerializer
    permission_classes = [permissions.IsAuthenticated, IsInventoryManagerOrAdmin]
    filterset_class = OrdenAutomaticaFilter

    def get_queryset(self):
        qs = super().get_queryset()
        estado = self.request.query_params.get("estado")
        if estado:
            qs = qs.filter(estado=estado)
        return qs

    def perform_create(self, serializer):
        instance = serializer.save()
        # Puedes emitir una señal aquí si deseas procesar tareas de forma asíncrona
        return instance

    def destroy(self, request, *args, **kwargs):
        orden = self.get_object()
        if orden.estado in ['completada', 'usada']:
            raise ValidationError("No se puede eliminar una orden completada o usada.")
        orden.estado = 'eliminada'
        orden.save()
        return Response({"detalle": "Orden marcada como eliminada."}, status=status.HTTP_204_NO_CONTENT)

# Creación del viewset ORDENAUTOMATICA-ITEM
@extend_schema_view(
    list=extend_schema(
        summary="Listar ítems de órdenes automáticas",
        description="Devuelve los productos incluidos en las órdenes automáticas. Se puede filtrar por ID de orden.",
        tags=["Ítems de Órdenes"]
    ),
    retrieve=extend_schema(
        summary="Obtener detalle de un ítem de orden",
        description="Muestra la información específica de un ítem dentro de una orden automática.",
        tags=["Ítems de Órdenes"]
    ),
    create=extend_schema(
        summary="Agregar ítem a una orden automática",
        description="Agrega un producto a una orden automática pendiente. Valida alerta, stock y coherencia del producto.",
        tags=["Ítems de Órdenes"]
    ),
    update=extend_schema(
        summary="Actualizar ítem de orden",
        description="Permite modificar un ítem solo si la orden se encuentra en estado pendiente.",
        tags=["Ítems de Órdenes"]
    ),
    partial_update=extend_schema(
        summary="Actualizar parcialmente un ítem de orden",
        description="Permite modificar algunos campos del ítem si la orden está pendiente.",
        tags=["Ítems de Órdenes"]
    ),
    destroy=extend_schema(
        summary="Eliminar ítem de orden",
        description="Elimina un ítem de orden solo si la orden asociada está en estado pendiente.",
        tags=["Ítems de Órdenes"]
    ),
)
class OrdenAutomaticaItemViewSet(viewsets.ModelViewSet):
    queryset = OrdenAutomaticaItem.objects.select_related(
        'producto', 'alerta', 'orden'
    ).all()
    serializer_class = OrdenAutomaticaItemSerializer
    permission_classes = [IsInventoryManagerOrAdmin]

    def get_queryset(self):
        queryset = super().get_queryset()
        orden_id = self.request.query_params.get("orden")
        if orden_id:
            queryset = queryset.filter(orden_id=orden_id)
        return queryset

    def perform_create(self, serializer):
        orden = serializer.validated_data.get('orden')
        if orden.estado != 'pendiente':
            raise ValidationError("No se pueden agregar ítems a una orden que no está en estado pendiente.")
        return serializer.save()

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.orden.estado != 'pendiente':
            raise ValidationError("No se pueden modificar ítems de una orden que no está pendiente.")
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.orden.estado != 'pendiente':
            raise ValidationError("No se pueden eliminar ítems de una orden que no está pendiente.")
        return super().destroy(request, *args, **kwargs)

# Creacion del viewset ENTRADA-INVENTARIO
@extend_schema_view(
    list=extend_schema(
        summary="Listar entradas de inventario",
        description="Devuelve todas las entradas de productos registradas en el sistema. Incluye datos del producto, proveedor y orden asociada si existe.",
        tags=["Entradas de Inventario"]
    ),
    retrieve=extend_schema(
        summary="Detalle de una entrada de inventario",
        description="Muestra la información completa de una entrada, incluyendo producto, cantidad, precio, total y proveedor.",
        tags=["Entradas de Inventario"]
    ),
    create=extend_schema(
        summary="Registrar una entrada de inventario",
        description="Registra el ingreso de productos al inventario. Si la entrada proviene de una orden automática, esta debe estar completada y no haber sido utilizada antes.",
        tags=["Entradas de Inventario"]
    ),
    update=extend_schema(
        summary="Actualizar entrada",
        description="Permite modificar entradas manuales (sin orden asociada). Las entradas generadas desde órdenes no se pueden editar.",
        tags=["Entradas de Inventario"]
    ),
    partial_update=extend_schema(
        summary="Actualizar parcialmente una entrada",
        description="Modifica campos específicos como la cantidad o el precio. No está permitido si la entrada tiene una orden asociada.",
        tags=["Entradas de Inventario"]
    ),
    destroy=extend_schema(
        summary="Eliminar entrada",
        description="Elimina una entrada de inventario y revierte el stock del producto si no está vinculada a una orden automática.",
        tags=["Entradas de Inventario"]
    ),
)
class EntradaInventarioViewSet(viewsets.ModelViewSet):
    queryset = EntradaInventario.objects.select_related(
        'producto', 'orden', 'proveedor'
    ).all()
    serializer_class = EntradaInventarioSerializer
    permission_classes = [IsInventoryManagerOrAdmin]

    def perform_create(self, serializer):
        orden = serializer.validated_data.get('orden', None)

        if orden:
            if orden.estado != 'completada':
                raise ValidationError("Solo se puede registrar una entrada desde una orden completada.")
            if orden.usada_para_ingreso:
                raise ValidationError("Esta orden ya fue utilizada para generar una entrada de inventario.")

        entrada = serializer.save()

        # Marcar la orden como usada para ingreso si aplica
        if entrada.orden:
            entrada.orden.usada_para_ingreso = True
            entrada.orden.save(update_fields=['usada_para_ingreso'])

        # Actualizar stock del producto
        producto = entrada.producto
        producto.stock += entrada.cantidad
        producto.save(update_fields=['stock'])

        return entrada

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.orden:
            raise ValidationError("No se puede editar una entrada asociada a una orden automática.")
        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.orden:
            raise ValidationError("No se puede eliminar una entrada asociada a una orden automática.")
        
        # Revertir stock
        producto = instance.producto
        producto.stock = max(0, producto.stock - instance.cantidad)
        producto.save(update_fields=['stock'])

        return super().destroy(request, *args, **kwargs)

# Creacion del viewset SALIDA-INVENTARIO
@extend_schema_view(
    list=extend_schema(
        summary="Listar salidas de inventario",
        description="Muestra todas las salidas de productos del inventario, incluyendo motivo, responsable y fecha.",
        tags=["Salidas de Inventario"]
    ),
    retrieve=extend_schema(
        summary="Detalle de una salida de inventario",
        description="Devuelve la información detallada de una salida específica, como producto, cantidad, motivo y observación.",
        tags=["Salidas de Inventario"]
    ),
    create=extend_schema(
        summary="Registrar salida de inventario",
        description="Permite registrar una salida de productos por merma, consumo interno, devolución o ajuste. Valida stock disponible.",
        tags=["Salidas de Inventario"]
    ),
    update=extend_schema(
        summary="No permitido",
        description="No se permite la edición de salidas de inventario una vez registradas.",
        tags=["Salidas de Inventario"]
    ),
    partial_update=extend_schema(
        summary="No permitido",
        description="No se permite la modificación parcial de salidas de inventario.",
        tags=["Salidas de Inventario"]
    ),
    destroy=extend_schema(
        summary="Eliminar salida de inventario",
        description="Elimina una salida de inventario y repone automáticamente el stock del producto.",
        tags=["Salidas de Inventario"]
    ),
)
class SalidaInventarioViewSet(viewsets.ModelViewSet):
    queryset = SalidaInventario.objects.select_related(
        'producto', 'responsable'
    ).all()
    serializer_class = SalidaInventarioSerializer
    permission_classes = [IsInventoryManagerOrAdmin]

    def perform_create(self, serializer):
        producto = serializer.validated_data.get('producto')
        cantidad = serializer.validated_data.get('cantidad')

        if cantidad > producto.stock:
            raise ValidationError("No hay suficiente stock disponible para realizar la salida.")

        # Registrar salida y descontar stock
        salida = serializer.save(responsable=self.request.user)
        producto.stock -= cantidad
        producto.save(update_fields=['stock'])

        return salida

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        raise ValidationError("No se permite la modificación de registros de salida una vez creados.")

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        # Reponer el stock al eliminar la salida
        producto = instance.producto
        producto.stock += instance.cantidad
        producto.save(update_fields=['stock'])

        return super().destroy(request, *args, **kwargs)

# Creacion del viewset COTIZACION-PROVEEDOR
@extend_schema_view(
    list=extend_schema(
        summary="Listar cotizaciones de proveedores",
        description="Devuelve todas las cotizaciones asociadas a órdenes automáticas. Incluye estado, monto y archivo PDF si existe.",
        tags=["Cotizaciones de Proveedores"]
    ),
    retrieve=extend_schema(
        summary="Detalle de una cotización",
        description="Muestra los datos de una cotización específica, incluyendo orden relacionada, estado, monto y archivo.",
        tags=["Cotizaciones de Proveedores"]
    ),
    create=extend_schema(
        summary="Registrar cotización",
        description="Permite registrar una cotización solo si la orden automática está en estado pendiente.",
        tags=["Cotizaciones de Proveedores"]
    ),
    update=extend_schema(
        summary="Actualizar cotización",
        description="Modifica una cotización si aún no ha sido aceptada ni rechazada.",
        tags=["Cotizaciones de Proveedores"]
    ),
    partial_update=extend_schema(
        summary="Actualizar parcialmente una cotización",
        description="Modifica campos específicos como el monto o el archivo, si la cotización está pendiente.",
        tags=["Cotizaciones de Proveedores"]
    ),
    destroy=extend_schema(
        summary="Eliminar cotización",
        description="Elimina una cotización solo si su estado es pendiente. No se pueden borrar cotizaciones aceptadas o rechazadas.",
        tags=["Cotizaciones de Proveedores"]
    ),
)
class CotizacionProveedorViewSet(viewsets.ModelViewSet):
    queryset = CotizacionProveedor.objects.select_related("orden").all()
    serializer_class = CotizacionProveedorSerializer
    permission_classes = [IsInventoryManagerOrAdmin]

    def perform_create(self, serializer):
        orden = serializer.validated_data.get("orden")
        if orden.estado != "pendiente":
            raise ValidationError("Solo se pueden registrar cotizaciones para órdenes en estado pendiente.")
        return serializer.save()

    def update(self, request, *args, **kwargs):
        instance = self.get_object()

        if instance.estado in ["aceptada", "rechazada"]:
            raise ValidationError("No se puede modificar una cotización que ya ha sido aceptada o rechazada.")

        return super().update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()

        if instance.estado != "pendiente":
            raise ValidationError("Solo se pueden eliminar cotizaciones en estado pendiente.")

        return super().destroy(request, *args, **kwargs)

# Creacion del viewset HISTORIAL-PRECIO-PRODUCTO
@extend_schema_view(
    list=extend_schema(
        summary="Listar historial de precios",
        description="Muestra el historial de precios registrados por producto y proveedor. Ordenados por fecha descendente.",
        tags=["Historial de Precios"]
    ),
    retrieve=extend_schema(
        summary="Detalle de un registro de precio",
        description="Devuelve los detalles de un cambio de precio para un producto, incluyendo proveedor, precio y fecha.",
        tags=["Historial de Precios"]
    ),
    create=extend_schema(
        summary="Registrar nuevo precio",
        description="Permite registrar un nuevo precio histórico para un producto, incluyendo el proveedor asociado.",
        tags=["Historial de Precios"]
    ),
    update=extend_schema(
        summary="No permitido",
        description="El historial de precios es inmutable. No se permite su edición.",
        tags=["Historial de Precios"]
    ),
    partial_update=extend_schema(
        summary="No permitido",
        description="El historial de precios es inmutable. No se permite su edición parcial.",
        tags=["Historial de Precios"]
    ),
    destroy=extend_schema(
        summary="No permitido",
        description="El historial de precios no puede eliminarse.",
        tags=["Historial de Precios"]
    ),
)
class HistorialPrecioProductoViewSet(viewsets.ModelViewSet):
    queryset = HistorialPrecioProducto.objects.select_related("producto", "proveedor").all()
    serializer_class = HistorialPrecioProductoSerializer
    permission_classes = [IsInventoryManagerOrAdmin]

    def create(self, request, *args, **kwargs):
        producto = request.data.get("producto")
        precio = request.data.get("precio")

        if not producto or not precio:
            raise ValidationError("Producto y precio son requeridos.")

        return super().create(request, *args, **kwargs)

    def update(self, request, *args, **kwargs):
        raise ValidationError("El historial de precios no puede modificarse una vez registrado.")

    def destroy(self, request, *args, **kwargs):
        raise ValidationError("El historial de precios no puede eliminarse.")

# Creacion del viewset KIT
@extend_schema_view(
    list=extend_schema(
        summary="Listar kits de productos",
        description="Devuelve todos los kits registrados junto con sus productos asociados.",
        tags=["Kits"]
    ),
    retrieve=extend_schema(
        summary="Detalle de un kit",
        description="Muestra el detalle completo de un kit, incluyendo nombre, descripción e ítems.",
        tags=["Kits"]
    ),
    create=extend_schema(
        summary="Crear nuevo kit",
        description="Permite registrar un nuevo kit de productos, validando la unicidad del nombre.",
        tags=["Kits"]
    ),
    update=extend_schema(
        summary="Actualizar kit",
        description="Permite modificar los datos de un kit siempre que su nombre no esté duplicado.",
        tags=["Kits"]
    ),
    partial_update=extend_schema(
        summary="Actualizar parcialmente un kit",
        description="Modifica parcialmente los campos de un kit. Valida que el nuevo nombre no exista.",
        tags=["Kits"]
    ),
    destroy=extend_schema(
        summary="Eliminar kit",
        description="Elimina un kit existente del sistema. Asegúrese de que no esté en uso antes de eliminarlo.",
        tags=["Kits"]
    ),
)
class KitViewSet(viewsets.ModelViewSet):
    queryset = Kit.objects.prefetch_related("items__producto").all()
    serializer_class = KitSerializer
    permission_classes = [IsInventoryManagerOrAdmin]

    def perform_create(self, serializer):
        nombre = serializer.validated_data.get("nombre")
        if Kit.objects.filter(nombre__iexact=nombre).exists():
            raise ValidationError("Ya existe un kit con ese nombre.")
        return serializer.save()

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        nuevo_nombre = request.data.get("nombre", "").strip()
        if nuevo_nombre and Kit.objects.exclude(id=instance.id).filter(nombre__iexact=nuevo_nombre).exists():
            raise ValidationError("Ya existe otro kit con ese nombre.")
        return super().update(request, *args, **kwargs)

# Creacion del viewset KIT-ITEM
@extend_schema_view(
    list=extend_schema(
        summary="Listar ítems de kits",
        description="Retorna todos los productos asociados a kits registrados en el sistema.",
        tags=["Kit Items"]
    ),
    retrieve=extend_schema(
        summary="Detalle de un ítem de kit",
        description="Muestra información detallada de un producto dentro de un kit específico.",
        tags=["Kit Items"]
    ),
    create=extend_schema(
        summary="Agregar producto a un kit",
        description="Permite agregar un nuevo producto a un kit existente, validando duplicidad.",
        tags=["Kit Items"]
    ),
    update=extend_schema(
        summary="Actualizar ítem de kit",
        description="Modifica la información de un ítem ya asociado a un kit. Verifica que no haya duplicidad.",
        tags=["Kit Items"]
    ),
    partial_update=extend_schema(
        summary="Actualizar parcialmente ítem de kit",
        description="Modifica parcialmente los datos de un ítem de kit, validando duplicidad si se cambia el producto.",
        tags=["Kit Items"]
    ),
    destroy=extend_schema(
        summary="Eliminar ítem de kit",
        description="Elimina un producto asociado a un kit sin afectar el resto de los componentes.",
        tags=["Kit Items"]
    ),
)
class KitItemViewSet(viewsets.ModelViewSet):
    queryset = KitItem.objects.select_related("kit", "producto").all()
    serializer_class = KitItemSerializer
    permission_classes = [IsInventoryManagerOrAdmin]

    def perform_create(self, serializer):
        kit = serializer.validated_data.get("kit")
        producto = serializer.validated_data.get("producto")

        # Validar duplicidad dentro del mismo kit
        if KitItem.objects.filter(kit=kit, producto=producto).exists():
            raise ValidationError("Este producto ya está incluido en el kit.")

        return serializer.save()

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        nuevo_producto = request.data.get("producto", instance.producto.id)
        if KitItem.objects.exclude(id=instance.id).filter(kit=instance.kit_id, producto=nuevo_producto).exists():
            raise ValidationError("Ya existe otro ítem con ese producto en este kit.")
        return super().update(request, *args, **kwargs)
    
# Creacion del viewset AUDITORIA
@extend_schema_view(
    list=extend_schema(
        summary="Listar auditorías",
        description="Retorna todos los registros de auditoría del sistema. Solo accesible por administradores.",
        tags=["Auditoría"]
    ),
    retrieve=extend_schema(
        summary="Detalle de auditoría",
        description="Muestra la información detallada de un registro de auditoría específico.",
        tags=["Auditoría"]
    ),
)
class AuditoriaViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Solo permite consultar registros de auditoría.
    No se permite crear, actualizar ni eliminar desde la API.
    """
    queryset = Auditoria.objects.select_related("usuario").all()
    serializer_class = AuditoriaSerializer
    permission_classes = [IsAdminUserOnly]

    def create(self, request, *args, **kwargs):
        raise ValidationError("Los registros de auditoría no pueden ser creados manualmente.")

    def update(self, request, *args, **kwargs):
        raise ValidationError("No está permitido modificar registros de auditoría.")

    def destroy(self, request, *args, **kwargs):
        raise ValidationError("No está permitido eliminar registros de auditoría.")
    
# Creacion del viewset NOTIFICACION
@extend_schema_view(
    list=extend_schema(
        summary="Listar notificaciones del usuario",
        description="Retorna todas las notificaciones del usuario autenticado. Solo lectura.",
        tags=["Notificaciones"]
    ),
    retrieve=extend_schema(
        summary="Detalle de una notificación",
        description="Muestra el contenido y estado de una notificación específica.",
        tags=["Notificaciones"]
    ),
)
class NotificacionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Permite listar y ver notificaciones del usuario autenticado.
    Incluye acción para marcar como leída.
    """
    serializer_class = NotificacionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        try:
            # Previene errores en modo documentación (swagger_fake_view)
            if getattr(self, 'swagger_fake_view', False):
                return Notificacion.objects.none()

            # Si no hay usuario autenticado, evita el crash
            if not self.request or not hasattr(self.request, "user") or self.request.user.is_anonymous:
                return Notificacion.objects.none()

            return Notificacion.objects.filter(usuario=self.request.user)

        except Exception as e:
            # Prevención total ante fallos inesperados
            import logging
            logger = logging.getLogger("django.request")
            logger.warning(f"Error en get_queryset de NotificacionViewSet: {e}")
            return Notificacion.objects.none()

    @action(detail=True, methods=["post"])
    def marcar_como_leida(self, request, pk=None):
        try:
            notificacion = self.get_object()

            if notificacion.usuario != request.user:
                raise ValidationError("No tiene permiso para modificar esta notificación.")

            if notificacion.leida:
                return Response({"detalle": "La notificación ya estaba marcada como leída."})

            notificacion.leida = True
            notificacion.save(update_fields=["leida"])
            return Response({"detalle": "Notificación marcada como leída."})

        except ValidationError as ve:
            raise ve  # se mantiene el flujo original de error válido
        except Exception as e:
            logger.warning(f"Error en marcar_como_leida: {e}")
            raise ValidationError("Ocurrió un error inesperado al marcar la notificación como leída.")

    def create(self, request, *args, **kwargs):
        try:
            raise ValidationError("Las notificaciones no pueden ser creadas manualmente.")
        except ValidationError as ve:
            raise ve
        except Exception as e:
            logger.error(f"Error en create de NotificacionViewSet: {e}")
            raise ValidationError("Error inesperado al intentar crear una notificación.")

    def destroy(self, request, *args, **kwargs):
        try:
            raise ValidationError("No se permite eliminar notificaciones desde el cliente.")
        except ValidationError as ve:
            raise ve
        except Exception as e:
            logger.error(f"Error en destroy de NotificacionViewSet: {e}")
            raise ValidationError("Error inesperado al intentar eliminar una notificación.")

# Creacion del viewset INVENTARIO-FISICO
@extend_schema_view(
    list=extend_schema(
        summary="Listar registros de inventario físico",
        description="Obtiene una lista de todos los conteos de inventario físico realizados.",
        tags=["Inventario Físico"]
    ),
    retrieve=extend_schema(
        summary="Detalle de un registro de inventario físico",
        description="Muestra los detalles de un conteo físico específico, incluyendo diferencia con el stock lógico.",
        tags=["Inventario Físico"]
    ),
    create=extend_schema(
        summary="Registrar nuevo inventario físico",
        description="Permite registrar un nuevo conteo de inventario físico, calculando automáticamente la diferencia con el stock actual.",
        tags=["Inventario Físico"]
    ),
)
class InventarioFisicoViewSet(viewsets.ModelViewSet):
    queryset = InventarioFisico.objects.select_related("producto", "responsable").all()
    serializer_class = InventarioFisicoSerializer
    permission_classes = [IsInventoryManagerOrAdmin]

    def perform_create(self, serializer):
        producto = serializer.validated_data.get("producto")
        stock_real = serializer.validated_data.get("stock_real")

        if stock_real is None:
            raise ValidationError("Debe especificar el stock real contado.")

        # Registro del conteo físico
        return serializer.save(responsable=self.request.user)

    def update(self, request, *args, **kwargs):
        raise ValidationError("No se permite modificar registros de inventario físico.")

    def destroy(self, request, *args, **kwargs):
        raise ValidationError("No se permite eliminar registros de inventario físico.")
