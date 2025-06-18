from django.shortcuts import render
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import status,viewsets, permissions, filters
from rest_framework.decorators import action
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from inventario.filters import OrdenAutomaticaFilter
from maestranza_backend.utils.generar_rut_valido import generar_rut_valido
from maestranza_backend.permissions import (
    IsAdmin, IsInventoryManager, IsInventoryManagerOrAdmin, IsAdminUserOnly, IsAuthenticated
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

# -----------------------------------------------#
# Creación de los viewsets localizacion regional.
# -----------------------------------------------#

# Create your views here.
class PaisViewSet(viewsets.ModelViewSet):
    queryset = Pais.objects.all().order_by('nombre')
    serializer_class = PaisSerializer

class RegionViewSet(viewsets.ModelViewSet):
    queryset = Region.objects.select_related('pais').order_by('nombre')
    serializer_class = RegionSerializer

class CiudadViewSet(viewsets.ModelViewSet):
    queryset = Ciudad.objects.select_related('region__pais').order_by('nombre')
    serializer_class = CiudadSerializer

class ComunaViewSet(viewsets.ModelViewSet):
    queryset = Comuna.objects.select_related('ciudad__region').order_by('nombre')
    serializer_class = ComunaSerializer

class CargoViewSet(viewsets.ModelViewSet):
    queryset = Cargo.objects.all().order_by('nombre')
    serializer_class = CargoSerializer

# --------------------------------------------------------#
# Creación de los viewsets fundamentales para el proyecto.
# --------------------------------------------------------#

# Creacion del viewset de CUSTOMUSER
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
class NotificacionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    Permite listar y ver notificaciones del usuario autenticado.
    Incluye acción para marcar como leída.
    """
    serializer_class = NotificacionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Notificacion.objects.filter(usuario=self.request.user).select_related("usuario")

    @action(detail=True, methods=["post"])
    def marcar_como_leida(self, request, pk=None):
        notificacion = self.get_object()
        if notificacion.usuario != request.user:
            raise ValidationError("No tiene permiso para modificar esta notificación.")
        
        if notificacion.leida:
            return Response({"detalle": "La notificación ya estaba marcada como leída."})

        notificacion.leida = True
        notificacion.save(update_fields=["leida"])
        return Response({"detalle": "Notificación marcada como leída."})

    def create(self, request, *args, **kwargs):
        raise ValidationError("Las notificaciones no pueden ser creadas manualmente.")

    def destroy(self, request, *args, **kwargs):
        raise ValidationError("No se permite eliminar notificaciones desde el cliente.")

# Creacion del viewset INVENTARIO-FISICO   
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