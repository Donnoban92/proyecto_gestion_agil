from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers
from maestranza_backend.utils.generar_rut_valido import generar_rut_valido
from inventario.validators import (
    validar_stock_minimo_no_negativo, validar_codigo_barra, validar_sku_formato,
    validar_fecha_fabricacion, validar_fechas_lote, 
    )
from .models import (
    Pais, Region, Ciudad, Comuna, Cargo, CustomUser,
    Categoria, Proveedor, Lote, Producto, AlertaStock, 
    OrdenAutomatica, OrdenAutomaticaItem, EntradaInventario,
    SalidaInventario, CotizacionProveedor, HistorialPrecioProducto,
    Kit, KitItem, Auditoria, Notificacion, InventarioFisico
    )


# --------------------------------------------------#
# Creación de los serializers localizacion regional.
# --------------------------------------------------#

class PaisSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pais
        fields = ["id", "nombre"]

class RegionSerializer(serializers.ModelSerializer):
    pais = PaisSerializer(read_only=True)
    pais_id = serializers.PrimaryKeyRelatedField(
        source='pais', queryset=Pais.objects.all(), write_only=True
    )

    class Meta:
        model = Region
        fields = ["id", "nombre", "pais", "pais_id"]

class CiudadSerializer(serializers.ModelSerializer):
    region = RegionSerializer(read_only=True)
    region_id = serializers.PrimaryKeyRelatedField(
        source='region', queryset=Region.objects.all(), write_only=True
    )

    class Meta:
        model = Ciudad
        fields = ["id", "nombre", "region", "region_id"]

class ComunaSerializer(serializers.ModelSerializer):
    ciudad = CiudadSerializer(read_only=True)
    ciudad_id = serializers.PrimaryKeyRelatedField(
        source='ciudad', queryset=Ciudad.objects.all(), write_only=True
    )

    class Meta:
        model = Comuna
        fields = ["id", "nombre", "ciudad", "ciudad_id"]

class CargoSerializer(serializers.ModelSerializer):
    class Meta:
        model = Cargo
        fields = ["id", "nombre"]

# -----------------------------------------------------------#
# Creación de los serializers fundamentales para el proyecto.
# -----------------------------------------------------------#

# Creacion del serializer CUSTOMUSER
class CustomUserSerializer(serializers.ModelSerializer):
    comuna = ComunaSerializer(read_only=True)
    comuna_id = serializers.PrimaryKeyRelatedField(
        source='comuna', queryset=Comuna.objects.all(), write_only=True
    )

    cargo = CargoSerializer(read_only=True)
    cargo_id = serializers.PrimaryKeyRelatedField(
        source='cargo', queryset=Cargo.objects.all(), write_only=True, allow_null=True
    )

    class Meta:
        model = CustomUser
        fields = [
            "id",
            "username",
            "first_name",
            "last_name",
            "correo",
            "rut",
            "telefono",
            "role",
            "direccion",
            "comuna", "comuna_id",
            "cargo", "cargo_id",
            "is_active",
            "date_joined",
        ]
        read_only_fields = ["date_joined"]

    def validate_rut(self, value):
        from maestranza_backend.utils.generar_rut_valido import generar_rut_valido
        try:
            if not generar_rut_valido(value):
                raise serializers.ValidationError("RUT inválido. Formato correcto: 12.345.678-9")
            return value.upper().replace(".", "")
        except Exception as e:
            raise serializers.ValidationError(f"Error al validar RUT: {str(e)}")

    def validate_telefono(self, value):
        try:
            telefono = value.strip().replace(" ", "").replace("-", "")
            if not telefono.startswith("+56"):
                telefono = "+56" + telefono.lstrip("+56")
            if not telefono[1:].isdigit() or len(telefono) < 11:
                raise serializers.ValidationError("El teléfono debe tener el formato +569XXXXXXXX")
            return telefono
        except Exception as e:
            raise serializers.ValidationError(f"Error al validar teléfono: {str(e)}")

    def validate_correo(self, value):
        try:
            existe = CustomUser.objects.filter(correo__iexact=value)
            if self.instance:
                existe = existe.exclude(id=self.instance.id)
            if existe.exists():
                raise serializers.ValidationError("Ya existe un usuario con este correo.")
            if self.instance and self.instance.correo != value:
                raise serializers.ValidationError("No está permitido modificar el correo una vez registrado.")
            return value
        except Exception as e:
            raise serializers.ValidationError(f"Error al validar correo: {str(e)}")

    def validate(self, data):
        try:
            role = data.get("role")
            cargo = data.get("cargo")
            if role in ["admin", "gestor_inventario", "jefe_produccion"] and not cargo:
                raise serializers.ValidationError({
                    "cargo_id": f"El rol '{role}' requiere asignación de un cargo específico."
                })
            return data
        except serializers.ValidationError as ve:
            raise ve
        except Exception as e:
            raise serializers.ValidationError(f"Error inesperado al validar el usuario: {str(e)}")

# Creacion del serializer CATEGORIA
class CategoriaSerializer(serializers.ModelSerializer):
    nombre = serializers.CharField(max_length=128)

    class Meta:
        model = Categoria
        fields = ['id', 'nombre', 'descripcion']

    def validate_nombre(self, value):
        try:
            nombre_normalizado = value.strip().lower()
            existe = Categoria.objects.filter(nombre__iexact=nombre_normalizado)
            if self.instance:
                existe = existe.exclude(id=self.instance.id)
            if existe.exists():
                raise serializers.ValidationError("Ya existe una categoría con este nombre.")
            return value.strip().title()
        except serializers.ValidationError as ve:
            raise ve
        except Exception as e:
            raise serializers.ValidationError(f"Error al validar nombre: {str(e)}")

    def validate_descripcion(self, value):
        try:
            return value.strip().capitalize() if value else value
        except Exception as e:
            raise serializers.ValidationError(f"Error al validar descripción: {str(e)}")

# Creacion del serializer PROVEEDOR
class ProveedorSerializer(serializers.ModelSerializer):
    comuna_nombre = serializers.CharField(source="comuna.nombre", read_only=True)

    class Meta:
        model = Proveedor
        fields = [
            'id',
            'nombre',
            'rut',
            'direccion',
            'comuna',
            'comuna_nombre',
            'telefono',
            'correo',
        ]

    def validate_nombre(self, value):
        try:
            return value.strip().title()
        except Exception as e:
            raise serializers.ValidationError(f"Error al validar nombre: {str(e)}")

    def validate_direccion(self, value):
        try:
            return value.strip().capitalize()
        except Exception as e:
            raise serializers.ValidationError(f"Error al validar dirección: {str(e)}")

    def validate_rut(self, value):
        try:
            rut = value.replace(".", "").replace("-", "").upper()
            if not generar_rut_valido(rut):
                raise serializers.ValidationError("RUT inválido. Formato correcto: 12.345.678-9")
            return rut
        except serializers.ValidationError as ve:
            raise ve
        except Exception as e:
            raise serializers.ValidationError(f"Error al validar RUT: {str(e)}")

    def validate_telefono(self, value):
        try:
            telefono = value.strip().replace(" ", "").replace("-", "")
            if not telefono.startswith("+56"):
                telefono = "+56" + telefono.lstrip("+56")
            if not telefono[1:].isdigit() or len(telefono) < 11:
                raise serializers.ValidationError("El teléfono debe tener el formato +569XXXXXXXX")
            return telefono
        except serializers.ValidationError as ve:
            raise ve
        except Exception as e:
            raise serializers.ValidationError(f"Error al validar teléfono: {str(e)}")

    def validate(self, data):
        try:
            correo = data.get("correo")
            if correo:
                existe = Proveedor.objects.filter(correo__iexact=correo)
                if self.instance:
                    existe = existe.exclude(id=self.instance.id)
                if existe.exists():
                    raise serializers.ValidationError({"correo": "Ya existe un proveedor con este correo."})
            return data
        except serializers.ValidationError as ve:
            raise ve
        except Exception as e:
            raise serializers.ValidationError(f"Error inesperado al validar proveedor: {str(e)}")

# Creacion del serializer LOTE
class LoteSerializer(serializers.ModelSerializer):
    proveedor_nombre = serializers.CharField(source="proveedor.nombre", read_only=True)
    categoria_nombre = serializers.CharField(source="categoria.nombre", read_only=True)

    class Meta:
        model = Lote
        fields = [
            'id',
            'codigo',
            'proveedor',
            'proveedor_nombre',
            'categoria',
            'categoria_nombre',
            'fecha_fabricacion',
            'fecha_vencimiento',
            'observaciones',
        ]
        read_only_fields = ['proveedor_nombre', 'categoria_nombre']

    def validate_codigo(self, value):
        try:
            if not value or not value.strip():
                raise serializers.ValidationError("El código del lote no puede estar vacío.")
            return value.strip().upper()
        except serializers.ValidationError as ve:
            raise ve
        except Exception as e:
            raise serializers.ValidationError(f"Error al validar código de lote: {str(e)}")

    def validate_fecha_fabricacion(self, value):
        try:
            return validar_fecha_fabricacion(value)
        except Exception as e:
            raise serializers.ValidationError(f"Error al validar fecha de fabricación: {str(e)}")

    def create(self, validated_data):
        try:
            validated_data["codigo"] = validated_data["codigo"].strip().upper()
            return super().create(validated_data)
        except Exception as e:
            raise serializers.ValidationError(f"Error al crear lote: {str(e)}")

    def update(self, instance, validated_data):
        try:
            validated_data.pop('codigo', None)
            return super().update(instance, validated_data)
        except Exception as e:
            raise serializers.ValidationError(f"Error al actualizar lote: {str(e)}")

    def validate(self, data):
        try:
            fecha_fab = data.get("fecha_fabricacion")
            fecha_venc = data.get("fecha_vencimiento")
            validar_fechas_lote(fecha_fab, fecha_venc)
            return data
        except serializers.ValidationError as ve:
            raise ve
        except Exception as e:
            raise serializers.ValidationError(f"Error al validar fechas del lote: {str(e)}")

# Creacion del serializer PRODUCTO
class ProductoSerializer(serializers.ModelSerializer):
    lote_codigo = serializers.CharField(source="lote.codigo", read_only=True)
    proveedor_id = serializers.IntegerField(source="lote.proveedor.id", read_only=True)
    proveedor_nombre = serializers.CharField(source="lote.proveedor.nombre", read_only=True)
    categoria_id = serializers.IntegerField(source="lote.categoria.id", read_only=True)
    categoria_nombre = serializers.CharField(source="lote.categoria.nombre", read_only=True)
    is_low_stock = serializers.SerializerMethodField()

    class Meta:
        model = Producto
        fields = [
            'id',
            'nombre',
            'descripcion',
            'precio',
            'stock',
            'stock_minimo',
            'codigo_barra',
            'sku',
            'habilitado',
            'fecha_actualizacion',
            'lote',
            'lote_codigo',
            'proveedor_id',
            'proveedor_nombre',
            'categoria_id',
            'categoria_nombre',
            'is_low_stock',
        ]
        read_only_fields = ['fecha_actualizacion', 'sku']

    @extend_schema_field(bool)
    def get_is_low_stock(self, obj):
        try:
            return obj.stock <= obj.stock_minimo
        except Exception:
            return False

    def validate_precio(self, value):
        try:
            if value <= 0:
                raise serializers.ValidationError("El precio debe ser mayor a cero.")
            return value
        except Exception as e:
            raise serializers.ValidationError(f"Error al validar precio: {str(e)}")

    def validate_stock(self, value):
        try:
            if value < 0:
                raise serializers.ValidationError("El stock no puede ser negativo.")
            return value
        except Exception as e:
            raise serializers.ValidationError(f"Error al validar stock: {str(e)}")

    def validate_stock_minimo(self, value):
        try:
            return validar_stock_minimo_no_negativo(value)
        except Exception as e:
            raise serializers.ValidationError(f"Error al validar stock mínimo: {str(e)}")

    def validate_codigo_barra(self, value):
        try:
            return validar_codigo_barra(value)
        except Exception as e:
            raise serializers.ValidationError(f"Error al validar código de barra: {str(e)}")

    def validate_sku(self, value):
        try:
            return validar_sku_formato(value)
        except Exception as e:
            raise serializers.ValidationError(f"Error al validar SKU: {str(e)}")

    def validate(self, data):
        try:
            stock = data.get("stock", self.instance.stock if self.instance else 0)
            stock_minimo = data.get("stock_minimo", self.instance.stock_minimo if self.instance else 0)

            if stock_minimo > stock and self.instance is None:
                raise serializers.ValidationError(
                    "El stock mínimo no puede ser mayor al stock inicial."
                )
            return data
        except serializers.ValidationError as ve:
            raise ve
        except Exception as e:
            raise serializers.ValidationError(f"Error en validación general de producto: {str(e)}")

    def create(self, validated_data):
        try:
            if validated_data.get("sku") == "SKU-generico":
                pass  # Se generará automáticamente por signal
            return super().create(validated_data)
        except Exception as e:
            raise serializers.ValidationError(f"Error al crear producto: {str(e)}")

    def update(self, instance, validated_data):
        try:
            validated_data.pop('sku', None)
            return super().update(instance, validated_data)
        except Exception as e:
            raise serializers.ValidationError(f"Error al actualizar producto: {str(e)}")

# Creacion del serializer ALERTASTOCK
class AlertaStockSerializer(serializers.ModelSerializer):
    producto_id = serializers.IntegerField(source='producto.id', read_only=True)
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)
    sku = serializers.CharField(source='producto.sku', read_only=True)
    proveedor_nombre = serializers.CharField(source='producto.lote.proveedor.nombre', read_only=True)
    categoria_nombre = serializers.CharField(source='producto.lote.categoria.nombre', read_only=True)

    class Meta:
        model = AlertaStock
        fields = [
            'id',
            'producto',
            'producto_id',
            'producto_nombre',
            'sku',
            'proveedor_nombre',
            'categoria_nombre',
            'estado',
            'fecha_creacion',
            'fecha_actualizacion',
            'fecha_silencio',
            'orden_relacionada',
            'usada_para_orden',
        ]
        read_only_fields = ['fecha_creacion', 'fecha_actualizacion']

    def validate(self, data):
        try:
            estado = data.get("estado")
            if estado and estado not in dict(AlertaStock.ESTADOS).keys():
                raise serializers.ValidationError("Estado inválido para alerta.")
            return data
        except serializers.ValidationError as ve:
            raise ve
        except Exception as e:
            raise serializers.ValidationError(f"Error al validar la alerta: {str(e)}")

    def validate_producto(self, value):
        try:
            if value.stock > value.stock_minimo:
                raise serializers.ValidationError("No se puede crear una alerta para un producto con stock suficiente.")
            return value
        except serializers.ValidationError as ve:
            raise ve
        except Exception as e:
            raise serializers.ValidationError(f"Error al validar producto en alerta: {str(e)}")

# Creacion del serializer ORDENAUTOMATICA-ITEM
class OrdenAutomaticaItemSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)
    sku = serializers.CharField(source='producto.sku', read_only=True)

    class Meta:
        model = OrdenAutomaticaItem
        fields = [
            'id',
            'producto',
            'producto_nombre',
            'sku',
            'cantidad_ordenada',
            'alerta',
        ]

    def validate(self, data):
        try:
            alerta = data.get('alerta')
            producto = data.get('producto')
            cantidad = data.get('cantidad_ordenada')

            if not alerta or not producto:
                raise serializers.ValidationError("Producto y alerta son obligatorios.")

            if alerta.producto_id != producto.id:
                raise serializers.ValidationError("La alerta seleccionada no corresponde al producto.")

            if cantidad <= 0:
                raise serializers.ValidationError("La cantidad debe ser mayor que cero.")

            if alerta.estado not in ['activa', 'pendiente']:
                raise serializers.ValidationError("No se puede crear ítem con una alerta que no esté activa o pendiente.")

            return data

        except serializers.ValidationError as ve:
            raise ve  # Propaga validaciones explícitas

        except Exception as e:
            raise serializers.ValidationError(f"Error inesperado al validar ítem de orden: {str(e)}")

# Creacion del serializer ORDEN-AUTOMATICA
class OrdenAutomaticaSerializer(serializers.ModelSerializer):
    proveedor_nombre = serializers.CharField(source='proveedor.nombre', read_only=True)
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)
    sku = serializers.CharField(source='producto.sku', read_only=True)
    items = OrdenAutomaticaItemSerializer(many=True, read_only=True)

    class Meta:
        model = OrdenAutomatica
        fields = [
            'id',
            'proveedor',
            'proveedor_nombre',
            'producto',
            'producto_nombre',
            'sku',
            'cantidad_ordenada',
            'estado',
            'fecha_creacion',
            'fecha_actualizacion',
            'alerta',
            'usada_para_ingreso',
            'items',
        ]
        read_only_fields = ['fecha_creacion', 'fecha_actualizacion', 'items']

    def validate(self, data):
        try:
            producto = data.get('producto')
            proveedor = data.get('proveedor')
            alerta = data.get('alerta')
            cantidad = data.get('cantidad_ordenada')

            if not producto or not proveedor:
                raise serializers.ValidationError("Debe especificar producto y proveedor.")

            if cantidad is None or cantidad <= 0:
                raise serializers.ValidationError("La cantidad ordenada debe ser mayor que cero.")

            if alerta:
                if alerta.producto_id != producto.id:
                    raise serializers.ValidationError("La alerta no corresponde al producto indicado.")
                if alerta.estado not in ['activa', 'pendiente']:
                    raise serializers.ValidationError("La alerta asociada no está en un estado válido.")

            if producto.lote.proveedor_id != proveedor.id:
                raise serializers.ValidationError("El proveedor no coincide con el proveedor del producto.")

            if producto.stock <= 0 and not alerta:
                raise serializers.ValidationError(
                    "Este producto no tiene stock disponible y no está asociado a una alerta. "
                    "Considere revisar la alerta correspondiente antes de generar la orden."
                )

            return data

        except serializers.ValidationError as ve:
            raise ve  # Redispara validaciones esperadas

        except Exception as e:
            raise serializers.ValidationError(f"Error al validar orden automática: {str(e)}")

# Creacion del serializer ENTRADA-INVENTARIO
class EntradaInventarioSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)
    sku = serializers.CharField(source='producto.sku', read_only=True)
    proveedor_nombre = serializers.CharField(source='proveedor.nombre', read_only=True, default=None)
    orden_id = serializers.IntegerField(source='orden.id', read_only=True, default=None)

    class Meta:
        model = EntradaInventario
        fields = [
            'id',
            'producto',
            'producto_nombre',
            'sku',
            'cantidad',
            'precio_unitario',
            'total',
            'fecha',
            'orden',
            'orden_id',
            'proveedor',
            'proveedor_nombre',
        ]
        read_only_fields = ['fecha', 'total']

    def validate_cantidad(self, value):
        try:
            if value <= 0:
                raise serializers.ValidationError("La cantidad debe ser un valor positivo.")
            return value
        except Exception as e:
            raise serializers.ValidationError(f"Error al validar cantidad: {str(e)}")

    def validate_precio_unitario(self, value):
        try:
            if value < 0:
                raise serializers.ValidationError("El precio unitario no puede ser negativo.")
            return value
        except Exception as e:
            raise serializers.ValidationError(f"Error al validar precio unitario: {str(e)}")

    def create(self, validated_data):
        try:
            validated_data['total'] = validated_data['cantidad'] * validated_data['precio_unitario']
            return super().create(validated_data)
        except Exception as e:
            raise serializers.ValidationError(f"Error al crear entrada de inventario: {str(e)}")

    def update(self, instance, validated_data):
        try:
            if 'cantidad' in validated_data or 'precio_unitario' in validated_data:
                cantidad = validated_data.get('cantidad', instance.cantidad)
                precio_unitario = validated_data.get('precio_unitario', instance.precio_unitario)
                validated_data['total'] = cantidad * precio_unitario
            return super().update(instance, validated_data)
        except Exception as e:
            raise serializers.ValidationError(f"Error al actualizar entrada de inventario: {str(e)}")

# Creacion del serializer SALIDA-INVENTARIO
class SalidaInventarioSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)
    sku = serializers.CharField(source='producto.sku', read_only=True)
    responsable_nombre = serializers.CharField(source='responsable.get_full_name', read_only=True, default=None)

    class Meta:
        model = SalidaInventario
        fields = [
            'id',
            'producto',
            'producto_nombre',
            'sku',
            'cantidad',
            'motivo',
            'observacion',
            'fecha',
            'responsable',
            'responsable_nombre',
        ]
        read_only_fields = ['fecha']

    def validate_cantidad(self, value):
        try:
            if value <= 0:
                raise serializers.ValidationError("La cantidad debe ser positiva.")
            return value
        except Exception as e:
            raise serializers.ValidationError(f"Error al validar cantidad: {str(e)}")

    def validate(self, data):
        try:
            producto = data.get('producto')
            cantidad = data.get('cantidad')

            if producto and cantidad:
                if cantidad > producto.stock:
                    raise serializers.ValidationError("No hay suficiente stock para realizar la salida.")
            return data
        except serializers.ValidationError as ve:
            raise ve
        except Exception as e:
            raise serializers.ValidationError(f"Error al validar salida de inventario: {str(e)}")

# Creacion del serializer COTIZACION-PROVEEDOR  
class CotizacionProveedorSerializer(serializers.ModelSerializer):
    orden_id = serializers.IntegerField(source="orden.id", read_only=True)
    archivo_pdf_url = serializers.SerializerMethodField()

    class Meta:
        model = CotizacionProveedor
        fields = [
            "id",
            "orden",
            "orden_id",
            "fecha_creacion",
            "fecha_actualizacion",
            "estado",
            "monto",
            "archivo_pdf",
            "archivo_pdf_url",
        ]
        read_only_fields = ["fecha_creacion", "fecha_actualizacion"]

    @extend_schema_field(serializers.URLField)
    def get_archivo_pdf_url(self, obj):
        try:
            return obj.archivo_pdf.url if obj.archivo_pdf else None
        except Exception as e:
            return f"Error al obtener URL del archivo: {str(e)}"

    def validate_monto(self, value):
        try:
            if value <= 0:
                raise serializers.ValidationError("El monto debe ser un valor positivo.")
            return value
        except Exception as e:
            raise serializers.ValidationError(f"Error al validar monto: {str(e)}")

# Creacion del serializer HISTORIAL-PRECIO-PRODUCTO
class HistorialPrecioProductoSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source="producto.nombre", read_only=True)
    sku = serializers.CharField(source="producto.sku", read_only=True)
    proveedor_nombre = serializers.CharField(source="proveedor.nombre", read_only=True, default=None)

    class Meta:
        model = HistorialPrecioProducto
        fields = [
            "id",
            "producto",
            "producto_nombre",
            "sku",
            "proveedor",
            "proveedor_nombre",
            "precio",
            "fecha_registro",
        ]
        read_only_fields = ["fecha_registro"]

    def validate_precio(self, value):
        try:
            if value <= 0:
                raise serializers.ValidationError("El precio debe ser mayor que cero.")
            return value
        except Exception as e:
            raise serializers.ValidationError(f"Error al validar precio: {str(e)}")

# Creacion del serializer KIT-ITEM
class KitItemSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source="producto.nombre", read_only=True)
    sku = serializers.CharField(source="producto.sku", read_only=True)

    class Meta:
        model = KitItem
        fields = [
            "id",
            "producto",
            "producto_nombre",
            "sku",
            "cantidad",
        ]

    def validate_cantidad(self, value):
        try:
            if value <= 0:
                raise serializers.ValidationError("La cantidad debe ser mayor que cero.")
            return value
        except Exception as e:
            raise serializers.ValidationError(f"Error al validar cantidad: {str(e)}")

# Creacion del serializer KIT
class KitSerializer(serializers.ModelSerializer):
    items = KitItemSerializer(many=True, read_only=True)

    class Meta:
        model = Kit
        fields = [
            "id",
            "nombre",
            "descripcion",
            "items",
        ]

    def validate_nombre(self, value):
        try:
            if not value.strip():
                raise serializers.ValidationError("El nombre del kit no puede estar vacío.")
            return value.strip().title()
        except serializers.ValidationError as ve:
            raise ve
        except Exception as e:
            raise serializers.ValidationError(f"Error al validar nombre del kit: {str(e)}")

    def validate_descripcion(self, value):
        try:
            return value.strip().capitalize() if value else value
        except Exception as e:
            raise serializers.ValidationError(f"Error al validar descripción del kit: {str(e)}")

# Creacion del serializer AUDITORIA
class AuditoriaSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.CharField(source='usuario.get_full_name', read_only=True)

    class Meta:
        model = Auditoria
        fields = [
            'id',
            'usuario',
            'usuario_nombre',
            'modelo_afectado',
            'id_objeto',
            'accion',
            'fecha',
            'descripcion',
        ]
        read_only_fields = ['fecha']

    def validate_modelo_afectado(self, value):
        try:
            if not value.strip():
                raise serializers.ValidationError("El campo 'modelo_afectado' no puede estar vacío.")
            return value
        except Exception as e:
            raise serializers.ValidationError(f"Error al validar 'modelo_afectado': {str(e)}")

    def validate_descripcion(self, value):
        try:
            if not value.strip():
                raise serializers.ValidationError("La descripción de la acción es obligatoria.")
            return value
        except Exception as e:
            raise serializers.ValidationError(f"Error al validar descripción: {str(e)}")

    def validate_accion(self, value):
        try:
            acciones_validas = dict(Auditoria._meta.get_field('accion').choices).keys()
            if value not in acciones_validas:
                raise serializers.ValidationError(f"Acción inválida. Debe ser una de: {', '.join(acciones_validas)}.")
            return value
        except Exception as e:
            raise serializers.ValidationError(f"Error al validar acción: {str(e)}")

# Creacion del serializer NOTIFICACION
class NotificacionSerializer(serializers.ModelSerializer):
    usuario_nombre = serializers.CharField(source='usuario.get_full_name', read_only=True)

    class Meta:
        model = Notificacion
        fields = [
            'id',
            'usuario',
            'usuario_nombre',
            'mensaje',
            'leida',
            'fecha_creacion',
        ]

    def validate_mensaje(self, value):
        try:
            if not value.strip():
                raise serializers.ValidationError("El mensaje no puede estar vacío.")
            return value
        except Exception as e:
            raise serializers.ValidationError(f"Error al validar mensaje: {str(e)}")

# Creacion del serializer INVENTARIO-FISICO
class InventarioFisicoSerializer(serializers.ModelSerializer):
    producto_nombre = serializers.CharField(source='producto.nombre', read_only=True)
    responsable_nombre = serializers.CharField(source='responsable.get_full_name', read_only=True)
    diferencia = serializers.IntegerField(read_only=True)

    def validate_stock_real(self, value):
        try:
            if value < 0:
                raise serializers.ValidationError("El stock real no puede ser negativo.")
            return value
        except Exception as e:
            raise serializers.ValidationError(f"Error al validar stock real: {str(e)}")

    class Meta:
        model = InventarioFisico
        fields = [
            'id',
            'producto',
            'producto_nombre',
            'stock_real',
            'fecha_conteo',
            'responsable',
            'responsable_nombre',
            'diferencia',
        ]
