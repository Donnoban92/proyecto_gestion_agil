# Python Standard Library
import locale
import re
from io import BytesIO
from datetime import timedelta

# Django Core
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django.core.validators import MinLengthValidator, RegexValidator
from django.db import models
from django.http import FileResponse, Http404
from django.utils import timezone

# Django REST Framework
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView

# Local Validators
from .validators import (
    validar_precio_positivo, validar_stock_no_negativo, validar_stock_minimo_no_negativo
    )

locale.setlocale(locale.LC_TIME, "es_CL.utf8")
comprobantes_storage = FileSystemStorage(location="media/comprobantes/")

# --------------------------------------------------------#
# Creacion de los modelos de manejo de datos geográficos.
# --------------------------------------------------------#

# Creacion del modelo PAIS
class Pais(models.Model):
    nombre = models.CharField(max_length=64, unique=True)
  
    class Meta:
        verbose_name = "País"
        verbose_name_plural = "Países"

    def __str__(self):
        return self.nombre
    
# Creacion del modelo REGION
class Region(models.Model):
    nombre = models.CharField(max_length=64)
    pais = models.ForeignKey(Pais, on_delete=models.CASCADE, related_name="regiones")

    class Meta:
        verbose_name = "Región"
        verbose_name_plural = "Regiones"

    def __str__(self):
        return self.nombre

# Creacion del modelo CIUDAD
class Ciudad(models.Model):
    nombre = models.CharField(max_length=64)
    region = models.ForeignKey(
        Region, on_delete=models.CASCADE, related_name="ciudades"
    )
    class Meta:
        verbose_name = "Ciudad"
        verbose_name_plural = "Ciudades"

    def __str__(self):
        return f"{self.nombre}, {self.region.nombre}"


# Creacion del modelo COMUNA
class Comuna(models.Model):
    nombre = models.CharField(max_length=64)
    ciudad = models.ForeignKey(Ciudad, on_delete=models.CASCADE, related_name="comunas")

    class Meta:
        verbose_name = "Comuna"
        verbose_name_plural = "Comunas"

    def __str__(self):
        return f"{self.nombre}, {self.ciudad.nombre}"

class Cargo(models.Model):
    nombre = models.CharField(max_length=32, unique=True)

    class Meta:
        verbose_name = "Cargo"
        verbose_name_plural = "Cargos"

    def __str__(self):
        return self.nombre

# --------------------------------------------------------#
# Creación de los modelos fundamentales para el proyecto.
# --------------------------------------------------------#

# Creacion del modelo USUARIO
class CustomUser(AbstractUser):
    class Roles(models.TextChoices):
        ADMIN = "ADMIN", "Administrador"
        INVENTARIO = "INVENTARIO", "Gestor de Inventario"
        COMPRADOR = "COMPRADOR", "Comprador"
        LOGISTICA = "LOGISTICA", "Encargado de Logística"
        PRODUCCION = "PRODUCCION", "Jefe de Producción"
        AUDITOR = "AUDITOR", "Auditor"
        PROYECTOS = "PROYECTOS", "Gerente de Proyectos"
        PLANTA = "PLANTA", "Trabajador de Planta"

    cargo = models.ForeignKey(
        Cargo, on_delete=models.SET_NULL, null=True, help_text="Nombre del cargo"
    )
    correo = models.EmailField(
        max_length=64,
        unique=True,
        help_text="ejemplo@correo.cl",
        default="usuario-temporal@correo.cl",
    )
    rut = models.CharField(
        max_length=12, unique=True, help_text="Formato: 12.345.678-9"
    )
    telefono = models.CharField(max_length=16, help_text="Formato: +56912345678")
    role = models.CharField(max_length=16, choices=Roles.choices, default=Roles.PLANTA)
    direccion = models.CharField(max_length=128)
    comuna = models.ForeignKey(
        Comuna, on_delete=models.SET_NULL, null=True, help_text="Comuna del usuario"
    )

    def get_full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

    def clean(self):
        if not re.match(r"^\+569\d{8}$", self.telefono):
            raise ValidationError(["Teléfono debe seguir el formato +569XXXXXXXX"])
        if not self.validate_rut(self.rut):
            raise ValidationError(["RUT inválido. Formato correcto: 12.345.678-9"])

    @staticmethod
    def validate_rut(rut):
        """Valida el RUT chileno con DV"""
        try:
            rut = rut.replace(".", "").replace("-", "").upper()
            cuerpo, dv = rut[:-1], rut[-1]

            if not cuerpo.isdigit():
                return False

            suma = 0
            multiplo = 2
            for c in reversed(cuerpo):
                suma += int(c) * multiplo
                multiplo = 2 if multiplo == 7 else multiplo + 1

            resto = 11 - (suma % 11)
            dv_calculado = "0" if resto == 11 else "K" if resto == 10 else str(resto)

            return dv_calculado == dv
        except:
            return False

    def save(self, *args, **kwargs):
        self.clean()
        if self.telefono and not self.telefono.startswith("+56"):
            self.telefono = f'+56{self.telefono.lstrip("+")}'
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.username} ({self.get_full_name() or 'Sin nombre'})"

    class Meta:
        verbose_name = "Usuario"
        verbose_name_plural = "Usuarios"
        ordering = ["date_joined"]
        indexes = [
            models.Index(fields=["rut"]),
            models.Index(fields=["username"]),
        ]

# Creacion del modelo CATEGORIA
class Categoria(models.Model):
    nombre = models.CharField(max_length=128, unique=True)
    descripcion = models.TextField(blank=True)

    class Meta:
        verbose_name = "Categoría"
        verbose_name_plural = "Categorías"

    def __str__(self):
        return self.nombre

# Creacion del modelo PROVEEDOR
class Proveedor(models.Model):
    nombre = models.CharField(max_length=128, unique=True)
    rut = models.CharField(
        max_length=12, unique=True, help_text="Formato: 76.453.678-1"
    )
    direccion = models.CharField(max_length=128)
    comuna = models.ForeignKey(Comuna, on_delete=models.SET_NULL, null=True)
    telefono = models.CharField(max_length=16, blank=True, help_text="+56911223344")
    correo = models.EmailField(
        max_length=64,
        unique=True,
        help_text="ejemplo@correo.cl",
        default="usuario-temporal@correo.cl",
    )

    def save(self, *args, **kwargs):
        if self.telefono:
            # Limpiar cualquier prefijo existente
            cleaned_phone = self.telefono.lstrip("+")
            if cleaned_phone.startswith("56"):
                # Si ya tiene 56, solo agregamos el +
                self.telefono = f"+{cleaned_phone}"
            else:
                # Si no tiene 56, agregamos +56
                self.telefono = f"+56{cleaned_phone}"
        super().save(*args, **kwargs)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Proveedor"
        verbose_name_plural = "Proveedores"
        ordering = ["id"]

# Creación del modelo LOTE
class Lote(models.Model):
    codigo = models.CharField(max_length=64, unique=True, help_text="Código único del lote")
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT, related_name="lotes")
    categoria = models.ForeignKey(Categoria, on_delete=models.PROTECT, related_name="lotes")
    fecha_fabricacion = models.DateField(null=True, blank=True)
    fecha_vencimiento = models.DateField(null=True, blank=True)
    observaciones = models.TextField(blank=True)

    def __str__(self):
        return f"Lote {self.codigo} - {self.proveedor.nombre}"

    class Meta:
        verbose_name = "Lote"
        verbose_name_plural = "Lotes"
        ordering = ["-fecha_fabricacion"]
        indexes = [
            models.Index(fields=["codigo"]),
            models.Index(fields=["fecha_vencimiento"]),
        ]

# Creacion del modelo PRODUCTO
class Producto(models.Model):
    nombre = models.CharField(max_length=128)
    descripcion = models.TextField(blank=True)
    lote = models.ForeignKey(Lote, on_delete=models.PROTECT, related_name="productos")
    precio = models.PositiveIntegerField(validators=[validar_precio_positivo])
    stock = models.PositiveIntegerField(validators=[validar_stock_no_negativo])
    stock_minimo = models.PositiveIntegerField(default=20, validators=[validar_stock_minimo_no_negativo])
    codigo_barra = models.CharField(
        max_length=64, unique=True, validators=[MinLengthValidator(8)]
    )
    sku = models.CharField(
        max_length=64, unique=True, default="SKU-generico"
    )  # Identificador único
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    habilitado = models.BooleanField(default=True)

    def is_stock_bajo(self):
        return self.stock <= self.stock_minimo

    def __str__(self):
        return self.nombre

    class Meta:
        ordering = ["id"]
        verbose_name = "Producto"
        verbose_name_plural = "Productos"
        indexes = [
            models.Index(fields=["nombre"]),
            models.Index(fields=["codigo_barra"]),
            models.Index(fields=["sku"]),
    ]
        
# Creacion del modelo de ALERTA-AUTOMATICA
class AlertaStock(models.Model):
    ESTADOS = [
        ("activa", "Activa"),
        ("pendiente", "Pendiente"),
        ("archivada", "Archivada"),
        ("silenciada", "Silenciada"),
        ("inactiva", "Inactiva"),
    ]
    
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True, null=True)
    fecha_silencio = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(
        max_length=32, 
        choices=ESTADOS,
        default="activa"
    )
    orden_relacionada = models.ForeignKey(
        'OrdenAutomatica', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True
    )
    usada_para_orden = models.BooleanField(default=False)

    def __str__(self):
        return f"Alerta de stock: {self.producto.nombre} - Estado: {self.estado}"

    class Meta:
        verbose_name = "Alerta de Stock"
        verbose_name_plural = "Alertas de Stock"
        ordering = ['-fecha_creacion']

# Creacion del modelo ORDEN-AUTOMATICA
class OrdenAutomatica(models.Model):
    ESTADOS = [
        ("pendiente", "Pendiente"), 
        ("completada", "Completada"),
        ('cancelada','Cancelada'),
        ('eliminada','Eliminada'),
        ('anulada','Anulada'),
        ('rechazada','Rechazada'),
        ("inactiva", "Inactiva"),
        ]
    alerta = models.ForeignKey(AlertaStock, on_delete=models.SET_NULL, null=True, blank=True)
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT, null=True,blank=True)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.PROTECT)
    cantidad_ordenada = models.PositiveIntegerField(default=0)
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True, null=True)
    estado = models.CharField(max_length=32, choices=ESTADOS, default="pendiente")
    usada_para_ingreso = models.BooleanField(default=False)

    def __str__(self):
        return f"Orden Automática para proveedor {self.proveedor.nombre} - Estado: {self.estado}"
    
    class Meta:
        verbose_name = "Orden Automática"
        verbose_name_plural = "Órdenes Automáticas"
        ordering = ["-fecha_creacion"]

# Creacion del modelo ORDEN-AUTOMATICA-ITEM
class OrdenAutomaticaItem(models.Model):
    orden = models.ForeignKey(OrdenAutomatica, related_name="items", on_delete=models.CASCADE)
    alerta = models.ForeignKey(AlertaStock, on_delete=models.PROTECT)
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad_ordenada = models.PositiveIntegerField()

    class Meta:
        verbose_name = "Ítem de Orden"
        verbose_name_plural = "Ítems de Órdenes"

# Creacion del modelo ENTRADA-INVENTARIO
class EntradaInventario(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    orden = models.ForeignKey(
        OrdenAutomatica, on_delete=models.SET_NULL, null=True, blank=True
    )
    proveedor = models.ForeignKey(
        Proveedor, on_delete=models.SET_NULL, null=True, blank=True
    )
    cantidad = models.PositiveBigIntegerField()
    fecha = models.DateTimeField(auto_now_add=True)
    precio_unitario = models.PositiveIntegerField(default=0)
    total = models.PositiveIntegerField(default=0)

    def __str__(self):
        return (
            f"Entrada {self.cantidad} x {self.producto.nombre} - "
            f"{self.fecha.strftime('%d de %m de %Y').capitalize()}"
        )
    
    class Meta:
        verbose_name = "Entrada de Inventario"
        verbose_name_plural = "Entradas de Inventario"
        ordering = ["-fecha"]

# Creacion del modelo SALIDA-INVENTARIO
class SalidaInventario(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    cantidad = models.PositiveIntegerField()
    fecha = models.DateTimeField(auto_now_add=True)
    motivo = models.CharField(
        max_length=128,
        choices=[
            ('merma', 'Merma/Pérdida'),
            ('consumo', 'Consumo Interno'),
            ('devolucion', 'Devolución a Proveedor'),
            ('ajuste', 'Ajuste Manual'),
        ]
    )
    responsable = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    observacion = models.TextField(blank=True)

    def __str__(self):
        return (
            f"Salida {self.cantidad} x {self.producto.nombre} - "
            f"{self.fecha.strftime('%d de %m de %Y').capitalize() if self.fecha else 'Sin fecha'}"
        )
        
    class Meta:
        verbose_name = "Salida de Inventario"
        verbose_name_plural = "Salidas de Inventario"
        ordering = ["-fecha"]

# Creacion del modelo COTIZACION-PROVEEDOR
class CotizacionProveedor(models.Model):
    ESTADOS = [
        ("pendiente", "Pendiente"),
        ("aceptada", "Aceptada"),
        ("rechazada", "Rechazada"),
    ]
    orden = models.ForeignKey(
        "OrdenAutomatica", on_delete=models.CASCADE, related_name="cotizaciones"
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True, null=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True, null=True)
    estado = models.CharField(max_length=16, choices=ESTADOS, default="pendiente")
    monto = models.PositiveIntegerField()
    archivo_pdf = models.FileField(upload_to="cotizaciones/pdf/", null=True, blank=True)

    def __str__(self):
        return f"Cotización #{self.id} - Orden {self.orden.id} ({self.estado})"
    
    class Meta:
        verbose_name = "Cotización de Proveedor"
        verbose_name_plural = "Cotizaciones de Proveedores"
        ordering = ["-fecha_creacion"]

# Creacion del modelo HISTORIAL-PRECIO
class HistorialPrecioProducto(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    proveedor = models.ForeignKey(Proveedor, on_delete=models.SET_NULL, null=True)
    precio = models.PositiveIntegerField()
    fecha_registro = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"${self.precio} para {self.producto.nombre} ({self.fecha_registro.date()})"

    class Meta:
        verbose_name = "Historial de Precio"
        verbose_name_plural = "Historiales de Precios"
        ordering = ["-fecha_registro"]

# Creacion del modelo KIT
class Kit(models.Model):
    nombre = models.CharField(max_length=128)
    descripcion = models.TextField(blank=True)

    def __str__(self):
        return self.nombre

    class Meta:
        verbose_name = "Kit de Productos"
        verbose_name_plural = "Kits de Productos"

# Creacion del modelo KIT-ITEM
class KitItem(models.Model):
    kit = models.ForeignKey(Kit, related_name="items", on_delete=models.CASCADE)
    producto = models.ForeignKey(Producto, on_delete=models.PROTECT)
    cantidad = models.PositiveIntegerField()

    def __str__(self):
        return f"{self.cantidad} x {self.producto.nombre} en {self.kit.nombre}"
    
    class Meta:
        verbose_name = "Ítem de Kit"
        verbose_name_plural = "Ítems de Kit"

# Creacion del modelo AUDITORIA
class Auditoria(models.Model):
    usuario = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    modelo_afectado = models.CharField(max_length=128)
    id_objeto = models.PositiveIntegerField()
    accion = models.CharField(
        max_length=32,
        choices=[('crear', 'Crear'), ('actualizar', 'Actualizar'), ('eliminar', 'Eliminar')]
    )
    fecha = models.DateTimeField(auto_now_add=True)
    descripcion = models.TextField()

    def __str__(self):
        return f"{self.usuario} - {self.accion} {self.modelo_afectado} ({self.id_objeto})"

    class Meta:
        verbose_name = "Registro de Auditoría"
        verbose_name_plural = "Registros de Auditoría"
        ordering = ["-fecha"]

# Creacion del modelo NOTIFICACION
class Notificacion(models.Model):
    usuario = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    mensaje = models.TextField()
    leida = models.BooleanField(default=False)
    fecha_creacion = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Notificación para {self.usuario.username}"

    class Meta:
        verbose_name = "Notificación"
        verbose_name_plural = "Notificaciones"
        ordering = ["-fecha_creacion"]

# Creacion del modelo INVENTARIO-FISICO
class InventarioFisico(models.Model):
    producto = models.ForeignKey(Producto, on_delete=models.CASCADE)
    stock_real = models.PositiveIntegerField()
    fecha_conteo = models.DateTimeField(auto_now_add=True)
    responsable = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)
    diferencia = models.IntegerField()

    def save(self, *args, **kwargs):
        self.diferencia = self.stock_real - self.producto.stock
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Inventario físico de {self.producto.nombre} - Real: {self.stock_real}"

    class Meta:
        verbose_name = "Inventario Físico"
        verbose_name_plural = "Inventarios Físicos"
        ordering = ["-fecha_conteo"]
