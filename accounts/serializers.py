# accounts/serializers.py
from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
import re
import bleach

Usuario = get_user_model()


class RegistroSerializer(serializers.ModelSerializer):
    """Serializer para registro de usuario con validaciones de seguridad"""
    contrasena = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    correo = serializers.EmailField(required=True)
    telefono = serializers.CharField(required=True, max_length=15)
    preguntasecreta = serializers.CharField(required=True, max_length=255)
    respuestasecreta = serializers.CharField(write_only=True, required=True, max_length=255)
    nombre = serializers.CharField(required=True, max_length=150)
    apellidopaterno = serializers.CharField(required=True, max_length=150)
    apellidomaterno = serializers.CharField(required=True, max_length=150)

    class Meta:
        model = Usuario
        fields = ['username', 'correo', 'contrasena', 'nombre', 'apellidopaterno',
                  'apellidomaterno', 'telefono', 'preguntasecreta', 'respuestasecreta']

    def validate_username(self, value):
        """Validar username: solo alfanumérico y guiones bajos"""
        # Sanitizar entrada
        value = bleach.clean(value.strip())

        if not re.match(r'^[a-zA-Z0-9_]{3,30}$', value):
            raise serializers.ValidationError(
                'El nombre de usuario debe tener entre 3-30 caracteres y solo contener letras, números y guiones bajos'
            )

        if Usuario.objects.filter(username=value).exists():
            raise serializers.ValidationError('El nombre de usuario ya está en uso')

        return value

    def validate_correo(self, value):
        """Validar email"""
        # Sanitizar entrada
        value = bleach.clean(value.strip().lower())

        if Usuario.objects.filter(email=value).exists():
            raise serializers.ValidationError('El correo ya está registrado')

        return value

    def validate_telefono(self, value):
        """Validar teléfono: solo números y opcionalmente + al inicio"""
        # Sanitizar entrada
        value = bleach.clean(value.strip())

        if not re.match(r'^\+?[0-9]{10,15}$', value):
            raise serializers.ValidationError(
                'El teléfono debe contener entre 10-15 dígitos'
            )

        if Usuario.objects.filter(telefono=value).exists():
            raise serializers.ValidationError('El teléfono ya está registrado')

        return value

    def validate_nombre(self, value):
        """Validar nombre: solo letras y espacios"""
        # Sanitizar entrada contra XSS
        value = bleach.clean(value.strip())

        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]{1,150}$', value):
            raise serializers.ValidationError(
                'El nombre solo debe contener letras y espacios'
            )

        return value

    def validate_apellidopaterno(self, value):
        """Validar apellido paterno"""
        value = bleach.clean(value.strip())

        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]{1,150}$', value):
            raise serializers.ValidationError(
                'El apellido solo debe contener letras y espacios'
            )

        return value

    def validate_apellidomaterno(self, value):
        """Validar apellido materno"""
        value = bleach.clean(value.strip())

        if not re.match(r'^[a-zA-ZáéíóúÁÉÍÓÚñÑ\s]{1,150}$', value):
            raise serializers.ValidationError(
                'El apellido solo debe contener letras y espacios'
            )

        return value

    def validate_preguntasecreta(self, value):
        """Validar pregunta secreta"""
        value = bleach.clean(value.strip())

        if len(value) < 10:
            raise serializers.ValidationError(
                'La pregunta secreta debe tener al menos 10 caracteres'
            )

        return value

    def validate_respuestasecreta(self, value):
        """Validar respuesta secreta"""
        value = bleach.clean(value.strip())

        if len(value) < 4:
            raise serializers.ValidationError(
                'La respuesta secreta debe tener al menos 4 caracteres'
            )

        return value.lower()  # Normalizar a minúsculas para comparación


class LoginSerializer(serializers.Serializer):
    """Serializer para login"""
    email = serializers.EmailField(required=True)
    password = serializers.CharField(write_only=True, required=True)

    def validate_email(self, value):
        """Sanitizar email"""
        return bleach.clean(value.strip().lower())


class CambioContrasenaSerializer(serializers.Serializer):
    """Serializer para cambio de contraseña"""
    email = serializers.EmailField(required=True)
    contrasena_actual = serializers.CharField(write_only=True, required=True)
    nueva_contrasena = serializers.CharField(write_only=True, required=True, validators=[validate_password])

    def validate_email(self, value):
        return bleach.clean(value.strip().lower())

    def validate(self, attrs):
        """Validar que contraseñas sean diferentes"""
        if attrs.get('contrasena_actual') == attrs.get('nueva_contrasena'):
            raise serializers.ValidationError({
                'nueva_contrasena': 'La nueva contraseña debe ser diferente a la actual'
            })
        return attrs


class RecuperacionContrasenaSerializer(serializers.Serializer):
    """Serializer para recuperación de contraseña"""
    email = serializers.EmailField(required=True)
    respuestaSecreta = serializers.CharField(required=True, max_length=255)

    def validate_email(self, value):
        return bleach.clean(value.strip().lower())

    def validate_respuestaSecreta(self, value):
        return bleach.clean(value.strip().lower())


class RestablecerContrasenaSerializer(serializers.Serializer):
    """Serializer para restablecer contraseña"""
    tempToken = serializers.CharField(required=True)
    nuevaContrasena = serializers.CharField(write_only=True, required=True, validators=[validate_password])


class VerificarOTPSerializer(serializers.Serializer):
    """Serializer para verificar códigos OTP"""
    tempToken = serializers.CharField(required=True)
    codigo = serializers.CharField(required=True, min_length=6, max_length=6)

    def validate_codigo(self, value):
        """Validar que el código sea numérico"""
        if not value.isdigit():
            raise serializers.ValidationError('El código debe ser numérico')
        return value
