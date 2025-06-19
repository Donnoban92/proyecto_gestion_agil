from django.contrib import admin
from .models import (
    Producto, Categoria, Proveedor, Lote,
    EntradaInventario, SalidaInventario, InventarioFisico,
    AlertaStock, Notificacion, OrdenAutomatica, OrdenAutomaticaItem,
    Kit, KitItem, HistorialPrecioProducto, CotizacionProveedor,
    Auditoria, CustomUser, Pais, Region, Ciudad, Comuna, Cargo
)

# =======================
# ADMIN BÁSICO – CATALOGOS
# =======================

@admin.register(Categoria)
class CategoriaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre')
    search_fields = ('nombre',)

@admin.register(Pais)
class PaisAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre')
    search_fields = ('nombre',)

@admin.register(Region)
class RegionAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'pais')
    list_filter = ('pais',)
    search_fields = ('nombre',)

@admin.register(Ciudad)
class CiudadAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'region')
    list_filter = ('region',)
    search_fields = ('nombre',)

@admin.register(Comuna)
class ComunaAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'ciudad')
    list_filter = ('ciudad',)
    search_fields = ('nombre',)

@admin.register(Cargo)
class CargoAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre')
    search_fields = ('nombre',)

# =======================
# PRODUCTOS Y LOTES
# =======================

@admin.register(Producto)
class ProductoAdmin(admin.ModelAdmin):
    def stock_actual(self, obj):
        return obj.stock
    stock_actual.short_description = "Stock actual"

    def categoria(self, obj):
        return obj.lote.categoria.nombre if obj.lote and obj.lote.categoria else None
    categoria.short_description = "Categoría"

    list_display = ('id', 'nombre', 'sku', 'stock_actual', 'stock_minimo', 'precio', 'lote', 'categoria')
    list_filter = ('lote__categoria', 'lote__proveedor')
    search_fields = ('nombre', 'sku', 'codigo_barra')
    autocomplete_fields = ('lote',)
    ordering = ('nombre',)

@admin.register(Lote)
class LoteAdmin(admin.ModelAdmin):
    list_display = ('id', 'codigo', 'proveedor', 'fecha_fabricacion', 'fecha_vencimiento')
    list_filter = ('proveedor', 'fecha_vencimiento')
    search_fields = ('codigo',)

@admin.register(Proveedor)
class ProveedorAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre', 'rut', 'telefono', 'correo')
    search_fields = ('nombre', 'rut')
    ordering = ('nombre',)

# =======================
# ENTRADAS / SALIDAS / INVENTARIO FÍSICO
# =======================

@admin.register(EntradaInventario)
class EntradaInventarioAdmin(admin.ModelAdmin):
    list_display = ('id', 'producto', 'cantidad', 'proveedor', 'fecha')
    list_filter = ('proveedor',)
    autocomplete_fields = ('producto', 'proveedor')

@admin.register(SalidaInventario)
class SalidaInventarioAdmin(admin.ModelAdmin):
    list_display = ('id', 'producto', 'cantidad', 'responsable', 'motivo', 'fecha')
    list_filter = ('motivo',)
    autocomplete_fields = ('producto', 'responsable')

@admin.register(InventarioFisico)
class InventarioFisicoAdmin(admin.ModelAdmin):
    def stock_registrado(self, obj):
        return obj.producto.stock
    stock_registrado.short_description = "Stock registrado"

    def fecha(self, obj):
        return obj.fecha_conteo
    fecha.short_description = "Fecha"

    list_display = ('id', 'producto', 'stock_registrado', 'stock_real', 'diferencia', 'fecha')
    search_fields = ('producto__nombre',)

# =======================
# ALERTAS / NOTIFICACIONES
# =======================

@admin.register(AlertaStock)
class AlertaStockAdmin(admin.ModelAdmin):
    list_display = ('id', 'producto', 'estado', 'usada_para_orden', 'fecha_creacion')
    list_filter = ('estado', 'usada_para_orden')
    search_fields = ('producto__nombre',)

@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ('id', 'mensaje', 'fecha_creacion', 'leida')
    list_filter = ('leida',)
    search_fields = ('mensaje',)

# =======================
# ÓRDENES AUTOMÁTICAS
# =======================

class OrdenAutomaticaItemInline(admin.TabularInline):
    model = OrdenAutomaticaItem
    extra = 0
    autocomplete_fields = ('producto',)

@admin.register(OrdenAutomatica)
class OrdenAutomaticaAdmin(admin.ModelAdmin):
    list_display = ('id', 'producto', 'proveedor', 'cantidad_ordenada', 'estado', 'fecha_creacion')
    list_filter = ('estado',)
    search_fields = ('producto__nombre', 'proveedor__nombre', 'id')
    inlines = [OrdenAutomaticaItemInline]
    autocomplete_fields = ('producto', 'proveedor', 'alerta')

@admin.register(CotizacionProveedor)
class CotizacionProveedorAdmin(admin.ModelAdmin):
    def archivo(self, obj):
        return obj.archivo_pdf.name if obj.archivo_pdf else "—"
    archivo.short_description = "Archivo PDF"

    def fecha(self, obj):
        return obj.fecha_creacion
    fecha.short_description = "Fecha creación"

    list_display = ('id', 'orden', 'archivo', 'fecha')
    search_fields = ('orden__producto__nombre', 'orden__proveedor__nombre', 'id')
    autocomplete_fields = ('orden',)

# =======================
# KITS
# =======================

class KitItemInline(admin.TabularInline):
    model = KitItem
    extra = 0
    autocomplete_fields = ('producto',)

@admin.register(Kit)
class KitAdmin(admin.ModelAdmin):
    list_display = ('id', 'nombre')
    search_fields = ('nombre',)
    inlines = [KitItemInline]

# =======================
# HISTORIAL Y AUDITORÍA
# =======================

@admin.register(HistorialPrecioProducto)
class HistorialPrecioAdmin(admin.ModelAdmin):
    def fecha(self, obj):
        return obj.fecha_registro
    fecha.short_description = "Fecha"

    list_display = ('id', 'producto', 'proveedor', 'precio', 'fecha')
    list_filter = ('producto',)

@admin.register(Auditoria)
class AuditoriaAdmin(admin.ModelAdmin):
    list_display = ('id', 'accion', 'modelo_afectado', 'usuario', 'fecha')
    list_filter = ('modelo_afectado', 'usuario', 'accion')
    search_fields = ('modelo_afectado', 'usuario__username')

# =======================
# USUARIOS
# =======================

@admin.register(CustomUser)
class CustomUserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'rut', 'email', 'cargo', 'comuna', 'is_active', 'is_staff')
    list_filter = ('is_staff', 'is_superuser', 'cargo')
    search_fields = ('username', 'rut', 'email')
    autocomplete_fields = ('comuna', 'cargo')
