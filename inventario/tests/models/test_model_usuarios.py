import pytest
from django.core.exceptions import ValidationError
from django.contrib.auth.hashers import check_password
from inventario.models import CustomUser
from maestranza_backend.utils.generar_rut_valido import generar_rut_valido


@pytest.mark.django_db
class TestCustomUserModel:

    def test_creacion_usuario_valido(self, comuna, cargo):
        try:
            rut_valido = generar_rut_valido()
            usuario = CustomUser.objects.create_user(
                username="jdoe",
                password="secreto123",
                first_name="Juan",
                last_name="Doe",
                correo="jdoe@correo.cl",
                rut=rut_valido,
                telefono="+56912345678",
                direccion="Calle Falsa 123",
                comuna=comuna,
                cargo=cargo,
                role=CustomUser.Roles.INVENTARIO
            )
            assert usuario.id is not None
            assert usuario.username == "jdoe"
            assert usuario.get_full_name() == "Juan Doe"
            assert usuario.role == CustomUser.Roles.INVENTARIO
            assert usuario.comuna == comuna
            assert usuario.cargo == cargo
            assert usuario.correo == "jdoe@correo.cl"
            assert check_password("secreto123", usuario.password)
        except Exception as e:
            pytest.fail(f"Fallo en creación de usuario válido: {e}")

    def test_error_por_telefono_invalido(self, comuna, cargo):
        try:
            rut_valido = generar_rut_valido()
            with pytest.raises(ValidationError) as error:
                CustomUser.objects.create_user(
                    username="usuario_invalido",
                    password="test123",
                    first_name="Error",
                    last_name="Telefono",
                    correo="error@correo.cl",
                    rut=rut_valido,
                    telefono="123456789",
                    direccion="Error calle",
                    comuna=comuna,
                    cargo=cargo,
                )
            assert "Teléfono debe seguir el formato +569XXXXXXXX" in str(error.value)
        except Exception as e:
            pytest.fail(f"Fallo en validación de teléfono inválido: {e}")

    def test_error_por_rut_invalido(self, comuna, cargo):
        try:
            with pytest.raises(ValidationError) as error:
                CustomUser.objects.create_user(
                    username="usuario_rut_mal",
                    password="test123",
                    first_name="Error",
                    last_name="Rut",
                    correo="rut@correo.cl",
                    rut="12345678-K",
                    telefono="+56912345678",
                    direccion="Dirección falsa",
                    comuna=comuna,
                    cargo=cargo,
                )
            assert "RUT inválido" in str(error.value)
        except Exception as e:
            pytest.fail(f"Fallo en validación de RUT inválido: {e}")

    def test_telefono_se_formatea_si_no_tiene_prefijo(self, comuna, cargo):
        try:
            rut_valido = generar_rut_valido()
            user = CustomUser.objects.create_user(
                username="no_prefijo",
                password="abc123",
                first_name="Test",
                last_name="Prefijo",
                correo="prefijo@correo.cl",
                rut=rut_valido,
                telefono="912345678",
                direccion="Av. 123",
                comuna=comuna,
                cargo=cargo,
            )
            assert user.telefono == "+56912345678"
        except Exception as e:
            pytest.fail(f"Fallo al formatear teléfono sin prefijo: {e}")

    def test_default_correo_se_asigna(self, comuna, cargo):
        try:
            rut_valido = generar_rut_valido()
            user = CustomUser.objects.create_user(
                username="sin_correo",
                password="abc123",
                first_name="Sin",
                last_name="Correo",
                rut=rut_valido,
                telefono="+56912345678",
                direccion="Av. Test",
                comuna=comuna,
                cargo=cargo,
            )
            assert user.correo == "usuario-temporal@correo.cl"
        except Exception as e:
            pytest.fail(f"Fallo al asignar correo por defecto: {e}")

    def test_str_retorna_formato_correcto(self, comuna, cargo):
        try:
            rut_valido = generar_rut_valido()
            user = CustomUser.objects.create_user(
                username="testuser",
                password="abc123",
                first_name="Ana",
                last_name="Torres",
                rut=rut_valido,
                telefono="+56912345678",
                direccion="Calle 456",
                comuna=comuna,
                cargo=cargo,
            )
            assert str(user) == "testuser (Ana Torres)"
        except Exception as e:
            pytest.fail(f"Fallo en método __str__: {e}")
