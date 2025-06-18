from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import (
    PaisViewSet, RegionViewSet, CiudadViewSet, ComunaViewSet, CargoViewSet,
    CustomUserViewSet, CategoriaViewSet, ProveedorViewSet, LoteViewSet, ProductoViewSet,
    AlertaStockViewSet, OrdenAutomaticaViewSet, OrdenAutomaticaItemViewSet,
    EntradaInventarioViewSet, SalidaInventarioViewSet, CotizacionProveedorViewSet,
    HistorialPrecioProductoViewSet, KitViewSet, KitItemViewSet, AuditoriaViewSet,
    NotificacionViewSet, InventarioFisicoViewSet
)

# Instancia principal del router
router = DefaultRouter()
router.register(r'paises', PaisViewSet)
router.register(r'regiones', RegionViewSet)
router.register(r'ciudades', CiudadViewSet)
router.register(r'comunas', ComunaViewSet)
router.register(r'cargos', CargoViewSet)
router.register(r'usuarios', CustomUserViewSet)
router.register(r'categorias', CategoriaViewSet)
router.register(r'proveedores', ProveedorViewSet)
router.register(r'lotes', LoteViewSet)
router.register(r'productos', ProductoViewSet)
router.register(r'alertas', AlertaStockViewSet)
router.register(r'ordenes', OrdenAutomaticaViewSet)
router.register(r'ordenes-items', OrdenAutomaticaItemViewSet)
router.register(r'entradas', EntradaInventarioViewSet)
router.register(r'salidas', SalidaInventarioViewSet)
router.register(r'cotizaciones', CotizacionProveedorViewSet)
router.register(r'historial-precios', HistorialPrecioProductoViewSet)
router.register(r'kits', KitViewSet)
router.register(r'kits-items', KitItemViewSet)
router.register(r'auditorias', AuditoriaViewSet)
router.register(r'notificaciones', NotificacionViewSet)
router.register(r'inventario-fisico', InventarioFisicoViewSet)

urlpatterns = [
    path('api/', include(router.urls)),
    # JWT Autenticacion
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),

]
