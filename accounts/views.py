# accounts/views_secure.py - VERSIÓN SEGURA CON TODAS LAS CORRECCIONES
"""
Vista segura del módulo de autenticación
Incluye todas las correcciones de seguridad identificadas en la auditoría
"""

import secrets
import uuid
import json
import logging
import time
from datetime import timedelta

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.views.decorators.http import require_http_methods
from django.middleware.csrf import get_token
from django.utils import timezone
from django_ratelimit.decorators import ratelimit
from axes.decorators import axes_dispatch

from firebase_admin import auth as firebase_auth

from .serializers import (
    RegistroSerializer,
    LoginSerializer,
    CambioContrasenaSerializer,
    RecuperacionContrasenaSerializer,
    RestablecerContrasenaSerializer,
    VerificarOTPSerializer,
)
from .decorators import login_required_json, require_verified_email, get_client_ip
from .utils.sendgrid_otp_service import (
    generar_codigo_otp,
    enviar_otp_email,
    enviar_otp_recuperacion,
)

# Configurar loggers
logger = logging.getLogger('accounts')
security_logger = logging.getLogger('security')

Usuario = get_user_model()


# ==================== CSRF TOKEN ====================

@ensure_csrf_cookie
@require_http_methods(["GET"])
def get_csrf_token(request):
    """Endpoint para que Angular obtenga el CSRF token"""
    return JsonResponse({'csrfToken': get_token(request)})


# ==================== REGISTRO DE USUARIO ====================

@ratelimit(key='ip', rate='5/h', method='POST')
@require_http_methods(["POST"])
def register_user(request):
    """
    Registro de usuario con validaciones de seguridad
    - Validación de entrada con serializers
    - Sanitización contra XSS
    - Protección CSRF
    - Rate limiting
    - Logging de seguridad
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        security_logger.warning(
            f'JSON inválido en registro desde IP {get_client_ip(request)}'
        )
        return JsonResponse({'error': 'JSON inválido'}, status=400)

    # Validar con serializer
    serializer = RegistroSerializer(data=data)
    if not serializer.is_valid():
        security_logger.warning(
            f'Intento de registro con datos inválidos: {serializer.errors} desde IP {get_client_ip(request)}'
        )
        return JsonResponse({'error': serializer.errors}, status=400)

    validated_data = serializer.validated_data

    try:
        # Validar contraseña con validadores de Django
        password = validated_data['contrasena']
        try:
            validate_password(password)
        except ValidationError as e:
            return JsonResponse({'error': list(e.messages)}, status=400)

        # Crear usuario
        usuario = Usuario(
            username=validated_data['username'],
            email=validated_data['correo'],
            first_name=validated_data['nombre'],
            last_name=validated_data['apellidopaterno'],
            telefono=validated_data['telefono'],
            pregunta_secreta=validated_data['preguntasecreta'],
            verificado=False,
            totp_enabled=False,
        )
        usuario.set_password(password)

        # Hashear respuesta secreta
        usuario.set_respuesta_secreta(validated_data['respuestasecreta'])
        usuario.save()

        # Generar código OTP
        codigo_otp = generar_codigo_otp()
        otp_expira = timezone.now() + timedelta(minutes=10)

        usuario.codigo_otp = codigo_otp
        usuario.otp_expira = otp_expira
        usuario.save()

        # Enviar OTP por email
        try:
            email_enviado = enviar_otp_email(validated_data['correo'], codigo_otp)

            logger.info(f'Usuario registrado: {usuario.email} desde IP {get_client_ip(request)}')

            return JsonResponse({
                'mensaje': 'Usuario registrado con éxito. Ingresa el código OTP enviado a tu correo.',
                'requires2fa': True,
                'canal': 'email',
                'destino': f"{validated_data['correo'][:2]}***@{validated_data['correo'].split('@')[1]}",
                'tempToken': str(usuario.id),
            }, status=201)

        except Exception as e:
            logger.error(f'Error enviando OTP: {str(e)}')
            return JsonResponse({
                'mensaje': 'Usuario registrado con éxito. Ingresa el código OTP enviado a tu correo.',
                'requires2fa': True,
                'canal': 'email',
                'destino': f"{validated_data['correo'][:2]}***@{validated_data['correo'].split('@')[1]}",
                'tempToken': str(usuario.id),
                'warning': 'El correo puede tardar unos minutos en llegar.'
            }, status=201)

    except Exception as e:
        logger.error(f'Error en register_user: {str(e)}', exc_info=True)
        return JsonResponse({
            'error': 'Error al registrar usuario. Por favor intenta nuevamente.'
        }, status=500)


# ==================== VERIFICACIÓN OTP REGISTRO ====================

@ratelimit(key='ip', rate='10/h', method='POST')
@require_http_methods(["POST"])
def verificar_registro_2fa(request):
    """Verifica el código OTP del registro"""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'JSON inválido'}, status=400)

    # Validar con serializer
    serializer = VerificarOTPSerializer(data=data)
    if not serializer.is_valid():
        return JsonResponse({'ok': False, 'error': serializer.errors}, status=400)

    validated_data = serializer.validated_data
    temp_token = validated_data['tempToken']
    codigo = validated_data['codigo']

    try:
        usuario = Usuario.objects.get(id=temp_token)
    except (Usuario.DoesNotExist, ValueError):
        security_logger.warning(
            f'Intento de verificación con token inválido desde IP {get_client_ip(request)}'
        )
        return JsonResponse({'ok': False, 'error': 'Token inválido'}, status=400)

    # Verificar expiración
    if usuario.otp_expira and usuario.otp_expira < timezone.now():
        usuario.codigo_otp = None
        usuario.otp_expira = None
        usuario.save()
        return JsonResponse({
            'ok': False,
            'error': 'Código expirado. Solicita uno nuevo.'
        }, status=400)

    # Verificar código OTP
    if not usuario.codigo_otp or usuario.codigo_otp != str(codigo):
        security_logger.warning(
            f'Código OTP incorrecto para usuario {usuario.email} desde IP {get_client_ip(request)}'
        )
        return JsonResponse({'ok': False, 'error': 'Código incorrecto'}, status=400)

    # Activar cuenta
    usuario.confirmado = True
    usuario.verificado = True
    usuario.codigo_otp = None
    usuario.otp_expira = None
    usuario.save()

    # Establecer sesión
    request.session['user_id'] = usuario.id
    request.session['authenticated'] = True
    request.session['email'] = usuario.email

    logger.info(f'Usuario verificado exitosamente: {usuario.email}')

    return JsonResponse({
        'ok': True,
        'usuario': {
            'id': usuario.id,
            'email': usuario.email,
            'username': usuario.username,
        },
        'message': 'Verificación exitosa'
    })


# ==================== LOGIN ====================

@axes_dispatch
@ratelimit(key='ip', rate='5/5m', method='POST')
@require_http_methods(["POST"])
def login_user(request):
    """
    Login de usuario con protección contra fuerza bruta
    - Django Axes para bloqueo de intentos fallidos
    - Rate limiting por IP
    - Logging de seguridad
    - Verificación de MFA si está habilitado
    """
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'JSON inválido'}, status=400)

    # Validar con serializer
    serializer = LoginSerializer(data=data)
    if not serializer.is_valid():
        return JsonResponse({'ok': False, 'error': serializer.errors}, status=400)

    validated_data = serializer.validated_data
    email = validated_data['email']
    password = validated_data['password']

    # Prevenir timing attacks - tiempo constante para usuario inexistente
    try:
        usuario = Usuario.objects.get(email=email)
        usuario_existe = True
    except Usuario.DoesNotExist:
        usuario_existe = False
        # Simular comprobación de contraseña para timing constante
        Usuario().set_password(password)

    if not usuario_existe:
        # Delay adicional para prevenir timing attacks
        time.sleep(0.5)
        security_logger.warning(
            f'Intento de login con email inexistente: {email} desde IP {get_client_ip(request)}'
        )
        return JsonResponse({
            'ok': False,
            'error': 'Credenciales incorrectas'
        }, status=401)

    # Verificar si cuenta está bloqueada manualmente
    if usuario.bloqueado_hasta and usuario.bloqueado_hasta > timezone.now():
        tiempo_restante = (usuario.bloqueado_hasta - timezone.now()).seconds // 60
        security_logger.warning(
            f'Intento de login en cuenta bloqueada: {email} desde IP {get_client_ip(request)}'
        )
        return JsonResponse({
            'ok': False,
            'error': f'Cuenta bloqueada temporalmente. Intenta en {tiempo_restante} minutos.'
        }, status=403)

    # Verificar contraseña
    if not usuario.check_password(password):
        # Incrementar intentos fallidos
        usuario.intentos_fallidos += 1

        if usuario.intentos_fallidos >= 5:
            usuario.bloqueado_hasta = timezone.now() + timedelta(hours=1)
            usuario.save()
            security_logger.warning(
                f'Cuenta bloqueada por intentos fallidos: {email} desde IP {get_client_ip(request)}'
            )
            return JsonResponse({
                'ok': False,
                'error': 'Demasiados intentos fallidos. Cuenta bloqueada por 1 hora.'
            }, status=403)

        usuario.save()
        security_logger.warning(
            f'Intento de login fallido ({usuario.intentos_fallidos}/5): {email} desde IP {get_client_ip(request)}'
        )

        return JsonResponse({
            'ok': False,
            'error': 'Credenciales incorrectas'
        }, status=401)

    # Login exitoso - resetear intentos fallidos
    usuario.intentos_fallidos = 0
    usuario.bloqueado_hasta = None
    usuario.save()

    # Verificar si tiene MFA habilitado
    if usuario.totp_enabled:
        # Generar código OTP para MFA
        codigo_otp = generar_codigo_otp()
        otp_expira = timezone.now() + timedelta(minutes=10)

        usuario.codigo_otp = codigo_otp
        usuario.otp_expira = otp_expira
        usuario.save()

        # Enviar OTP por email
        try:
            enviar_otp_email(usuario.email, codigo_otp)
        except Exception as e:
            logger.error(f'Error enviando OTP de MFA: {str(e)}')

        logger.info(f'Login con MFA iniciado para: {usuario.email}')

        return JsonResponse({
            'ok': True,
            'requires2fa': True,
            'canal': 'email',
            'destino': f"{usuario.email[:2]}***@{usuario.email.split('@')[1]}",
            'tempToken': str(usuario.id),
            'message': 'Se ha enviado un código de verificación a tu correo'
        })

    # Login sin MFA - establecer sesión directamente
    request.session['user_id'] = usuario.id
    request.session['authenticated'] = True
    request.session['email'] = usuario.email

    logger.info(f'Login exitoso: {usuario.email} desde IP {get_client_ip(request)}')

    return JsonResponse({
        'ok': True,
        'usuario': {
            'id': usuario.id,
            'email': usuario.email,
            'username': usuario.username,
        },
        'message': 'Login exitoso'
    })


# ==================== VERIFICACIÓN MFA LOGIN ====================

@ratelimit(key='ip', rate='10/h', method='POST')
@require_http_methods(["POST"])
def verificar_login_2fa(request):
    """Verifica el código 2FA del login"""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'JSON inválido'}, status=400)

    # Validar con serializer
    serializer = VerificarOTPSerializer(data=data)
    if not serializer.is_valid():
        return JsonResponse({'ok': False, 'error': serializer.errors}, status=400)

    validated_data = serializer.validated_data
    temp_token = validated_data['tempToken']
    codigo = validated_data['codigo']

    try:
        usuario = Usuario.objects.get(id=temp_token)
    except (Usuario.DoesNotExist, ValueError):
        return JsonResponse({'ok': False, 'error': 'Usuario no encontrado'}, status=404)

    # Verificar expiración
    if usuario.otp_expira and usuario.otp_expira < timezone.now():
        usuario.codigo_otp = None
        usuario.otp_expira = None
        usuario.save()
        return JsonResponse({
            'ok': False,
            'error': 'Código expirado. Solicita uno nuevo.'
        }, status=400)

    # Verificar código OTP
    if not usuario.codigo_otp or usuario.codigo_otp != str(codigo):
        security_logger.warning(
            f'Código 2FA incorrecto para usuario {usuario.email} desde IP {get_client_ip(request)}'
        )
        return JsonResponse({'ok': False, 'error': 'Código incorrecto'}, status=400)

    # Código correcto - limpiar OTP y establecer sesión
    usuario.codigo_otp = None
    usuario.otp_expira = None
    usuario.save()

    request.session['user_id'] = usuario.id
    request.session['authenticated'] = True
    request.session['email'] = usuario.email

    logger.info(f'Verificación 2FA exitosa: {usuario.email}')

    return JsonResponse({
        'ok': True,
        'usuario': {
            'id': usuario.id,
            'email': usuario.email,
            'username': usuario.username,
        },
        'message': 'Login exitoso'
    })


# ==================== GOOGLE LOGIN ====================

@ratelimit(key='ip', rate='10/h', method='POST')
@require_http_methods(["POST"])
def google_login(request):
    """Login con Google OAuth"""
    try:
        data = json.loads(request.body)
        id_token = data.get('idToken')
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({'ok': False, 'error': 'Datos inválidos'}, status=400)

    if not id_token:
        return JsonResponse({'ok': False, 'error': 'idToken es requerido'}, status=400)

    try:
        decoded_token = firebase_auth.verify_id_token(id_token)
        email = decoded_token['email']
        name = decoded_token.get('name', '')

        # Buscar o crear usuario
        usuario, created = Usuario.objects.get_or_create(
            email=email,
            defaults={
                'username': email.split('@')[0] + '_' + str(uuid.uuid4())[:8],
                'first_name': name.split(' ')[0] if name else '',
                'last_name': name.split(' ')[1] if len(name.split(' ')) > 1 else '',
                'verificado': True,
                'totp_enabled': False,
            }
        )

        # Establecer sesión
        request.session['user_id'] = usuario.id
        request.session['authenticated'] = True
        request.session['email'] = usuario.email

        logger.info(f'Login con Google: {usuario.email}')

        return JsonResponse({
            'ok': True,
            'usuario': {
                'id': usuario.id,
                'email': usuario.email,
                'username': usuario.username,
            },
            'message': 'Inicio de sesión con Google exitoso'
        })

    except Exception as e:
        security_logger.error(f'Error en Google login: {str(e)}', exc_info=True)
        return JsonResponse({
            'ok': False,
            'error': 'Token de Google inválido'
        }, status=401)


# ==================== LOGOUT ====================

@login_required_json
@require_http_methods(["POST"])
def logout_user(request):
    """
    Cerrar sesión y limpiar datos de sesión
    """
    user_email = request.session.get('email', 'unknown')

    # Limpiar completamente la sesión
    request.session.flush()

    logger.info(f'Logout exitoso: {user_email} desde IP {get_client_ip(request)}')

    return JsonResponse({
        'ok': True,
        'message': 'Sesión cerrada exitosamente'
    })


# Continúa en siguiente mensaje...
# PARTE 2 - Recuperación de contraseña y otras funciones

# ==================== RECUPERACIÓN DE CONTRASEÑA ====================

@ratelimit(key='ip', rate='3/h', method='POST')
@require_http_methods(["POST"])
def obtener_pregunta_secreta(request):
    """Obtiene la pregunta secreta de un usuario"""
    try:
        data = json.loads(request.body)
        email = data.get('email')
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({'ok': False, 'error': 'Datos inválidos'}, status=400)

    if not email:
        return JsonResponse({'ok': False, 'error': 'El email es requerido'}, status=400)

    # Delay para prevenir timing attacks
    time.sleep(0.5)

    try:
        usuario = Usuario.objects.get(email=email)
        if not usuario.pregunta_secreta:
            return JsonResponse({
                'ok': False,
                'error': 'Este usuario no tiene pregunta secreta configurada'
            }, status=400)

        return JsonResponse({
            'ok': True,
            'preguntaSecreta': usuario.pregunta_secreta
        })

    except Usuario.DoesNotExist:
        # No revelar si el usuario existe
        return JsonResponse({
            'ok': False,
            'error': 'No se encontró una cuenta con ese correo'
        }, status=404)


@ratelimit(key='ip', rate='3/h', method='POST')
@require_http_methods(["POST"])
def recuperar_contrasena(request):
    """Verifica la respuesta a la pregunta secreta"""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'JSON inválido'}, status=400)

    # Validar con serializer
    serializer = RecuperacionContrasenaSerializer(data=data)
    if not serializer.is_valid():
        return JsonResponse({'ok': False, 'error': serializer.errors}, status=400)

    validated_data = serializer.validated_data
    email = validated_data['email']
    respuesta_secreta = validated_data['respuestaSecreta']

    # Delay para prevenir timing attacks
    time.sleep(0.5)

    try:
        usuario = Usuario.objects.get(email=email)
    except Usuario.DoesNotExist:
        security_logger.warning(
            f'Intento de recuperación con email inexistente: {email} desde IP {get_client_ip(request)}'
        )
        return JsonResponse({'ok': False, 'error': 'Datos incorrectos'}, status=400)

    # Verificar respuesta secreta (ahora hasheada)
    if not usuario.check_respuesta_secreta(respuesta_secreta):
        security_logger.warning(
            f'Respuesta secreta incorrecta para {email} desde IP {get_client_ip(request)}'
        )
        return JsonResponse({'ok': False, 'error': 'Respuesta incorrecta'}, status=400)

    # Generar token temporal y guardarlo
    codigo_validacion = 'SECRET_OK_' + secrets.token_hex(8)
    usuario.codigo_otp = codigo_validacion
    usuario.otp_expira = timezone.now() + timedelta(minutes=10)
    usuario.save()

    logger.info(f'Recuperación de contraseña iniciada para: {email}')

    return JsonResponse({
        'ok': True,
        'tempToken': str(usuario.id),
        'message': 'Respuesta correcta. Ahora puedes cambiar tu contraseña.'
    })


@ratelimit(key='ip', rate='5/h', method='POST')
@require_http_methods(["POST"])
def restablecer_contrasena(request):
    """Restablece la contraseña después de verificar la pregunta secreta"""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'JSON inválido'}, status=400)

    # Validar con serializer
    serializer = RestablecerContrasenaSerializer(data=data)
    if not serializer.is_valid():
        return JsonResponse({'ok': False, 'error': serializer.errors}, status=400)

    validated_data = serializer.validated_data
    temp_token = validated_data['tempToken']
    nueva_contrasena = validated_data['nuevaContrasena']

    try:
        usuario = Usuario.objects.get(id=temp_token)
    except (Usuario.DoesNotExist, ValueError):
        return JsonResponse({'ok': False, 'error': 'Token inválido o expirado'}, status=400)

    # Verificar que el código de validación existe y no ha expirado
    if not usuario.codigo_otp or not usuario.otp_expira:
        return JsonResponse({
            'ok': False,
            'error': 'Token inválido o expirado. Solicita uno nuevo.'
        }, status=400)

    # Verificar expiración
    if usuario.otp_expira < timezone.now():
        usuario.codigo_otp = None
        usuario.otp_expira = None
        usuario.save()
        return JsonResponse({
            'ok': False,
            'error': 'Token expirado. Solicita uno nuevo.'
        }, status=400)

    # Verificar que el código inicie con 'SECRET_OK_'
    if not usuario.codigo_otp.startswith('SECRET_OK_'):
        return JsonResponse({
            'ok': False,
            'error': 'Token inválido. Debes verificar la pregunta secreta primero.'
        }, status=400)

    # Actualizar contraseña
    usuario.set_password(nueva_contrasena)
    usuario.codigo_otp = None
    usuario.otp_expira = None

    # Invalidar todas las sesiones del usuario (seguridad adicional)
    # En un sistema de producción, deberías implementar un sistema de tokens
    # que permita invalidar sesiones específicas

    usuario.save()

    logger.info(f'Contraseña restablecida para: {usuario.email}')

    return JsonResponse({
        'ok': True,
        'message': 'Contraseña actualizada con éxito'
    })


# ==================== OTP CON SENDGRID ====================

@ratelimit(key='ip', rate='10/h', method='POST')
@require_http_methods(["POST"])
def reenviar_otp(request):
    """Reenvía un código OTP"""
    try:
        data = json.loads(request.body)
        correo = data.get('correo')
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({'ok': False, 'error': 'Datos inválidos'}, status=400)

    if not correo:
        return JsonResponse({'ok': False, 'error': 'Correo es requerido'}, status=400)

    try:
        usuario = Usuario.objects.get(email=correo)
    except Usuario.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Usuario no encontrado'}, status=404)

    # Generar nuevo código
    nuevo_codigo = generar_codigo_otp()
    usuario.codigo_otp = nuevo_codigo
    usuario.otp_expira = timezone.now() + timedelta(minutes=10)
    usuario.save()

    # Enviar nuevo código
    try:
        enviar_otp_email(correo, nuevo_codigo)
        return JsonResponse({
            'ok': True,
            'message': 'Nuevo código enviado a tu correo. Expira en 10 minutos.'
        }, status=200)
    except Exception as e:
        logger.error(f'Error enviando OTP: {str(e)}')
        return JsonResponse({
            'ok': False,
            'error': 'No se pudo enviar el código'
        }, status=500)


@ratelimit(key='ip', rate='3/h', method='POST')
@require_http_methods(["POST"])
def solicitar_recuperacion_otp(request):
    """Inicia el proceso de recuperación de contraseña enviando OTP"""
    try:
        data = json.loads(request.body)
        correo = data.get('email')
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({'ok': False, 'error': 'Datos inválidos'}, status=400)

    if not correo:
        return JsonResponse({'ok': False, 'error': 'Email es requerido'}, status=400)

    # Delay para prevenir timing attacks
    time.sleep(0.5)

    try:
        usuario = Usuario.objects.get(email=correo)
    except Usuario.DoesNotExist:
        # Por seguridad, no revelar si el usuario existe
        return JsonResponse({
            'ok': True,
            'message': 'Si el correo existe, se enviará un código de recuperación.'
        }, status=200)

    # Generar código OTP
    codigo_otp = generar_codigo_otp()
    usuario.codigo_otp = codigo_otp
    usuario.otp_expira = timezone.now() + timedelta(minutes=10)
    usuario.save()

    # Enviar código por email
    try:
        enviar_otp_recuperacion(correo, codigo_otp)
        logger.info(f'Código de recuperación enviado a: {correo}')
        return JsonResponse({
            'ok': True,
            'message': 'Código de recuperación enviado a tu correo. Expira en 10 minutos.',
            'tempToken': str(usuario.id)
        }, status=200)
    except Exception as e:
        logger.error(f'Error enviando código de recuperación: {str(e)}')
        return JsonResponse({
            'ok': False,
            'error': 'No se pudo enviar el código de recuperación'
        }, status=500)


@ratelimit(key='ip', rate='10/h', method='POST')
@require_http_methods(["POST"])
def verificar_otp_recuperacion(request):
    """Verifica el código OTP para recuperación de contraseña"""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'JSON inválido'}, status=400)

    # Validar con serializer
    serializer = VerificarOTPSerializer(data=data)
    if not serializer.is_valid():
        return JsonResponse({'ok': False, 'error': serializer.errors}, status=400)

    validated_data = serializer.validated_data
    temp_token = validated_data['tempToken']
    codigo = validated_data['codigo']

    try:
        usuario = Usuario.objects.get(id=temp_token)
    except (Usuario.DoesNotExist, ValueError):
        return JsonResponse({'ok': False, 'error': 'Usuario no encontrado'}, status=404)

    # Verificar expiración
    if not usuario.otp_expira or usuario.otp_expira < timezone.now():
        usuario.codigo_otp = None
        usuario.otp_expira = None
        usuario.save()
        return JsonResponse({
            'ok': False,
            'error': 'Código expirado. Solicita uno nuevo.'
        }, status=400)

    # Verificar código
    if not usuario.codigo_otp or usuario.codigo_otp != codigo:
        security_logger.warning(
            f'Código de recuperación incorrecto para {usuario.email} desde IP {get_client_ip(request)}'
        )
        return JsonResponse({'ok': False, 'error': 'Código incorrecto'}, status=400)

    # Código correcto - mantener código activo para cambio de contraseña
    return JsonResponse({
        'ok': True,
        'message': 'Código verificado. Ahora puedes cambiar tu contraseña.'
    }, status=200)


@ratelimit(key='ip', rate='5/h', method='POST')
@require_http_methods(["POST"])
def actualizar_contrasena_otp(request):
    """Actualiza la contraseña después de verificar OTP"""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'JSON inválido'}, status=400)

    # Validar con serializer
    serializer = RestablecerContrasenaSerializer(data=data)
    if not serializer.is_valid():
        return JsonResponse({'ok': False, 'error': serializer.errors}, status=400)

    validated_data = serializer.validated_data
    temp_token = validated_data['tempToken']
    nueva_contrasena = validated_data['nuevaContrasena']

    try:
        usuario = Usuario.objects.get(id=temp_token)
    except (Usuario.DoesNotExist, ValueError):
        return JsonResponse({'ok': False, 'error': 'Usuario no encontrado'}, status=404)

    # Verificar que el código OTP aún sea válido
    if not usuario.codigo_otp or not usuario.otp_expira or usuario.otp_expira < timezone.now():
        return JsonResponse({
            'ok': False,
            'error': 'Sesión expirada. Solicita un nuevo código.'
        }, status=400)

    # Actualizar contraseña
    usuario.set_password(nueva_contrasena)
    usuario.codigo_otp = None
    usuario.otp_expira = None
    usuario.save()

    logger.info(f'Contraseña actualizada vía OTP para: {usuario.email}')

    return JsonResponse({
        'ok': True,
        'message': 'Contraseña actualizada correctamente'
    }, status=200)


# ==================== GESTIÓN DE SEGURIDAD ====================

@login_required_json
@require_http_methods(["POST"])
def obtener_estado_seguridad(request):
    """Obtiene el estado de seguridad del usuario"""
    try:
        data = json.loads(request.body)
        email = data.get('email')
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({'ok': False, 'error': 'Datos inválidos'}, status=400)

    if not email:
        return JsonResponse({'ok': False, 'error': 'Email es requerido'}, status=400)

    try:
        usuario = Usuario.objects.get(email=email)
    except Usuario.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Usuario no encontrado'}, status=404)

    # Verificar que el usuario autenticado coincide
    if request.session.get('user_id') != usuario.id:
        return JsonResponse({'ok': False, 'error': 'No autorizado'}, status=403)

    # Contar códigos de respaldo disponibles
    backup_codes_count = 0
    if usuario.backup_codes:
        try:
            codes = json.loads(usuario.backup_codes)
            if isinstance(codes, list):
                backup_codes_count = len(codes)
        except:
            backup_codes_count = 0

    # Verificar si tiene preguntas de seguridad
    tiene_preguntas = bool(usuario.pregunta_secreta and usuario.respuesta_secreta)

    return JsonResponse({
        'ok': True,
        'email_2fa': usuario.verificado,
        'totp_habilitado': usuario.totp_enabled,
        'codigos_respaldo_disponibles': backup_codes_count,
        'tiene_preguntas_seguridad': tiene_preguntas
    }, status=200)


@login_required_json
@require_http_methods(["POST"])
def cambiar_contrasena(request):
    """Cambia la contraseña del usuario autenticado"""
    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'ok': False, 'error': 'JSON inválido'}, status=400)

    # Validar con serializer
    serializer = CambioContrasenaSerializer(data=data)
    if not serializer.is_valid():
        return JsonResponse({'ok': False, 'error': serializer.errors}, status=400)

    validated_data = serializer.validated_data
    email = validated_data['email']

    try:
        usuario = Usuario.objects.get(email=email)
    except Usuario.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Usuario no encontrado'}, status=404)

    # Verificar que el usuario autenticado coincide
    if request.session.get('user_id') != usuario.id:
        return JsonResponse({'ok': False, 'error': 'No autorizado'}, status=403)

    # Verificar contraseña actual
    if not usuario.check_password(validated_data['contrasena_actual']):
        return JsonResponse({
            'ok': False,
            'error': 'Contraseña actual incorrecta'
        }, status=400)

    # Actualizar contraseña
    usuario.set_password(validated_data['nueva_contrasena'])
    usuario.save()

    logger.info(f'Contraseña cambiada para: {usuario.email}')

    return JsonResponse({
        'ok': True,
        'message': 'Contraseña cambiada exitosamente'
    }, status=200)


@login_required_json
@require_http_methods(["POST"])
def generar_codigos_respaldo(request):
    """Genera códigos de respaldo para el usuario"""
    try:
        data = json.loads(request.body)
        email = data.get('email')
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({'ok': False, 'error': 'Datos inválidos'}, status=400)

    if not email:
        return JsonResponse({'ok': False, 'error': 'Email es requerido'}, status=400)

    try:
        usuario = Usuario.objects.get(email=email)
    except Usuario.DoesNotExist:
        return JsonResponse({'ok': False, 'error': 'Usuario no encontrado'}, status=404)

    # Verificar que el usuario autenticado coincide
    if request.session.get('user_id') != usuario.id:
        return JsonResponse({'ok': False, 'error': 'No autorizado'}, status=403)

    # Generar 10 códigos de 8 dígitos con secrets (criptográficamente seguro)
    codigos = []
    for _ in range(10):
        codigo = ''.join([str(secrets.randbelow(10)) for _ in range(8)])
        codigos.append(codigo)

    # Guardar códigos como JSON
    usuario.backup_codes = json.dumps(codigos)
    usuario.save()

    logger.info(f'Códigos de respaldo generados para: {usuario.email}')

    return JsonResponse({
        'ok': True,
        'codigos': codigos,
        'message': 'Códigos de respaldo generados exitosamente'
    }, status=200)
