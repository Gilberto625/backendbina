# accounts/views.py
from firebase_admin import auth as firebase_auth
import uuid
import random
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.middleware.csrf import get_token
from django_ratelimit.decorators import ratelimit
import json
import datetime
from django.contrib.auth.hashers import check_password
import logging
import qrcode
import io
import base64
from .email_utils import enviar_correo_verificacion, enviar_correo_recuperacion, enviar_correo_bienvenida

Usuario = get_user_model()
logger = logging.getLogger(__name__)

def generar_codigo():
    return str(random.randint(100000, 999999))

@ensure_csrf_cookie
def get_csrf_token(request):
    """
    Endpoint para que Angular obtenga el CSRF token
    """
    return JsonResponse({'csrfToken': get_token(request)})

@csrf_exempt
def register_user(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({'error': 'JSON inválido'}, status=400)

    # Validar campos requeridos
    campos = ['nombre', 'apellidopaterno', 'apellidomaterno', 'username',
              'correo', 'contrasena', 'telefono', 'preguntasecreta', 'respuestasecreta']
    for c in campos:
        if not data.get(c):
            return JsonResponse({'error': f'El campo {c} es obligatorio'}, status=400)

    # Verificar unicidad
    if Usuario.objects.filter(username=data['username']).exists():
        return JsonResponse({'error': 'El nombre de usuario ya está en uso'}, status=400)
    if Usuario.objects.filter(email=data['correo']).exists():
        return JsonResponse({'error': 'El correo ya está registrado'}, status=400)
    if Usuario.objects.filter(telefono=data['telefono']).exists():
        return JsonResponse({'error': 'El teléfono ya está registrado'}, status=400)

    # Crear usuario
    usuario = Usuario(
        username=data['username'],
        email=data['correo'],
        first_name=data['nombre'],
        last_name=data['apellidopaterno'],
        telefono=data['telefono'],
        pregunta_secreta=data['preguntasecreta'],
        respuesta_secreta=data['respuestasecreta'],
        verificado=False,
    )
    usuario.set_password(data['contrasena'])
    usuario.save()

    # Generar y enviar código 2FA
    codigo = generar_codigo()
    temp_token = str(uuid.uuid4())
    request.session[temp_token] = {
        'email': data['correo'],
        'codigo': codigo,
        'intentos': 0,
        'expira': (datetime.datetime.now() + datetime.timedelta(minutes=5)).timestamp()
    }

    if not enviar_correo_verificacion(data['correo'], codigo):
        logger.error(f"Error al enviar correo de verificación a {data['correo']}")
        return JsonResponse({'error': 'No se pudo enviar el correo. Verifica tu email y vuelve a intentar.'}, status=500)

    return JsonResponse({
        'mensaje': 'Usuario registrado con éxito',
        'requires2fa': True,
        'canal': 'email',
        'destino': f"{data['correo'][:2]}***@{data['correo'].split('@')[1]}",
        'tempToken': temp_token,
    }, status=201)
@csrf_exempt
def verificar_registro_2fa(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
        temp_token = data.get('tempToken')
        codigo = data.get('codigo')
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({'error': 'Datos inválidos'}, status=400)

    if not temp_token or not codigo:
        return JsonResponse({'error': 'tempToken y codigo son requeridos'}, status=400)

    # Obtener datos de la sesión
    session_data = request.session.get(temp_token)
    if not session_data:
        return JsonResponse({'error': 'Sesión 2FA inválida'}, status=400)

    # Verificar expiración (5 minutos)
    if datetime.datetime.now().timestamp() > session_data.get('expira', 0):
        del request.session[temp_token]
        return JsonResponse({'error': 'Código expirado. Solicita uno nuevo'}, status=400)

    # Verificar código
    if session_data['codigo'] != str(codigo):
        session_data['intentos'] = session_data.get('intentos', 0) + 1
        request.session[temp_token] = session_data  # Guardar intentos

        if session_data['intentos'] >= 5:
            del request.session[temp_token]
            return JsonResponse({'error': 'Demasiados intentos'}, status=429)

        return JsonResponse({'error': 'Código incorrecto'}, status=400)

    # Código correcto: marcar usuario como verificado
    try:
        usuario = Usuario.objects.get(email=session_data['email'])
        usuario.verificado = True
        usuario.save()

        # Enviar correo de bienvenida
        enviar_correo_bienvenida(usuario.email, usuario.first_name)
        logger.info(f"Usuario {usuario.email} verificado exitosamente")
    except Usuario.DoesNotExist:
        return JsonResponse({'error': 'Usuario no encontrado'}, status=400)

    # Limpiar sesión
    del request.session[temp_token]

    return JsonResponse({'ok': True, 'mensaje': 'Verificación exitosa'})
@csrf_exempt
@ratelimit(key='ip', rate='5/m', method='POST')
def login_user(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({'error': 'Datos inválidos'}, status=400)

    if not email or not password:
        return JsonResponse({'error': 'Email y contraseña son requeridos'}, status=400)

    # Autenticar usuario
    try:
        usuario = Usuario.objects.get(email=email)
    except Usuario.DoesNotExist:
        return JsonResponse({'error': 'Credenciales inválidas'}, status=400)

    if not usuario.check_password(password):
        return JsonResponse({'error': 'Credenciales inválidas'}, status=400)

    # Si el usuario está verificado, requiere 2FA
    if usuario.verificado:
        temp_token = str(uuid.uuid4())

        # Determinar métodos disponibles
        metodos_disponibles = ['email']  # Email siempre disponible
        if usuario.totp_enabled:
            metodos_disponibles.append('totp')
        if usuario.backup_codes:
            metodos_disponibles.append('backup')

        # Si tiene TOTP habilitado, no enviamos código por email automáticamente
        # El usuario puede elegir qué método usar
        response_data = {
            'requires2fa': True,
            'tempToken': temp_token,
            'metodos_disponibles': metodos_disponibles,
        }

        # Solo enviar código por email si es el único método o el usuario lo solicita
        if 'totp' not in metodos_disponibles:
            # Usuario no tiene TOTP, enviar código por email
            codigo = generar_codigo()
            request.session[temp_token] = {
                'email': usuario.email,
                'codigo': codigo,
                'intentos': 0,
                'expira': (datetime.datetime.now() + datetime.timedelta(minutes=5)).timestamp()
            }

            if not enviar_correo_verificacion(usuario.email, codigo):
                logger.error(f"Error al enviar código de login a {usuario.email}")
                return JsonResponse({'error': 'No se pudo enviar el correo'}, status=500)

            logger.info(f"Código 2FA enviado a {usuario.email}")
            response_data['canal'] = 'email'
            response_data['destino'] = f"{email[:2]}***@{email.split('@')[1]}"
        else:
            # Usuario tiene TOTP, guardar solo el email en sesión
            request.session[temp_token] = {
                'email': usuario.email,
                'expira': (datetime.datetime.now() + datetime.timedelta(minutes=5)).timestamp()
            }
            response_data['mensaje'] = 'Usa tu app de autenticación o solicita un código por email'

        return JsonResponse(response_data)

    # Si no está verificado, genera JWT (más adelante lo haremos)
    return JsonResponse({
        'ok': True,
        'mensaje': 'Inicio de sesión exitoso',
        'usuario': {
            'id': usuario.id,
            'email': usuario.email,
            'username': usuario.username,
        }
    })
@csrf_exempt
def solicitar_codigo_email(request):
    """
    Solicita un código por email cuando el usuario tiene TOTP pero prefiere usar email
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
        temp_token = data.get('tempToken')
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({'error': 'Datos inválidos'}, status=400)

    if not temp_token:
        return JsonResponse({'error': 'tempToken es requerido'}, status=400)

    # Obtener datos de la sesión
    session_data = request.session.get(temp_token)
    if not session_data:
        return JsonResponse({'error': 'Sesión inválida'}, status=400)

    try:
        usuario = Usuario.objects.get(email=session_data['email'])
    except Usuario.DoesNotExist:
        return JsonResponse({'error': 'Usuario no encontrado'}, status=400)

    # Generar y enviar código
    codigo = generar_codigo()
    session_data['codigo'] = codigo
    session_data['intentos'] = 0
    session_data['expira'] = (datetime.datetime.now() + datetime.timedelta(minutes=5)).timestamp()
    request.session[temp_token] = session_data

    if not enviar_correo_verificacion(usuario.email, codigo):
        logger.error(f"Error al enviar código de login a {usuario.email}")
        return JsonResponse({'error': 'No se pudo enviar el correo'}, status=500)

    logger.info(f"Código por email solicitado para {usuario.email}")

    return JsonResponse({
        'ok': True,
        'canal': 'email',
        'destino': f"{usuario.email[:2]}***@{usuario.email.split('@')[1]}",
        'mensaje': 'Código enviado a tu correo'
    })


@csrf_exempt
def verificar_login_2fa(request):
    """
    Verifica códigos de 2FA durante el login
    Soporta: email (código de 6 dígitos), TOTP (Google Authenticator), backup codes
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
        temp_token = data.get('tempToken')
        codigo = data.get('codigo')
        tipo = data.get('tipo', 'email')  # email, totp, backup
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({'error': 'Datos inválidos'}, status=400)

    if not temp_token or not codigo:
        return JsonResponse({'error': 'tempToken y codigo son requeridos'}, status=400)

    # Obtener datos de la sesión
    session_data = request.session.get(temp_token)
    if not session_data:
        return JsonResponse({'error': 'Sesión 2FA inválida'}, status=400)

    # Verificar expiración (5 minutos)
    if datetime.datetime.now().timestamp() > session_data.get('expira', 0):
        del request.session[temp_token]
        return JsonResponse({'error': 'Sesión expirada. Inicia sesión de nuevo'}, status=400)

    # Obtener usuario
    try:
        usuario = Usuario.objects.get(email=session_data['email'])
    except Usuario.DoesNotExist:
        return JsonResponse({'error': 'Usuario no encontrado'}, status=400)

    # Verificar según el tipo
    if tipo == 'email':
        # Verificar código enviado por email
        if 'codigo' not in session_data:
            return JsonResponse({'error': 'No se ha enviado código por email. Solicita uno primero.'}, status=400)

        if session_data['codigo'] != str(codigo):
            session_data['intentos'] = session_data.get('intentos', 0) + 1
            request.session[temp_token] = session_data

            if session_data['intentos'] >= 5:
                del request.session[temp_token]
                logger.warning(f"Demasiados intentos fallidos para {usuario.email}")
                return JsonResponse({'error': 'Demasiados intentos'}, status=429)

            return JsonResponse({'error': 'Código incorrecto'}, status=400)

    elif tipo == 'totp':
        # Verificar código TOTP
        if not usuario.totp_enabled:
            return JsonResponse({'error': 'TOTP no está habilitado'}, status=400)

        if not usuario.verify_totp(codigo):
            logger.warning(f"Código TOTP incorrecto para {usuario.email}")
            return JsonResponse({'error': 'Código TOTP incorrecto'}, status=400)

    elif tipo == 'backup':
        # Verificar código de respaldo
        if not usuario.verify_backup_code(codigo):
            logger.warning(f"Código de respaldo incorrecto o ya usado para {usuario.email}")
            return JsonResponse({'error': 'Código de respaldo incorrecto o ya usado'}, status=400)

    else:
        return JsonResponse({'error': 'Tipo de código inválido'}, status=400)

    # Limpiar sesión
    del request.session[temp_token]

    logger.info(f"Login exitoso con {tipo} para {usuario.email}")

    return JsonResponse({
        'ok': True,
        'mensaje': 'Inicio de sesión exitoso',
        'usuario': {
            'id': usuario.id,
            'email': usuario.email,
            'username': usuario.username,
        }
    })
@csrf_exempt
def google_login(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
        id_token = data.get('idToken')
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({'error': 'Datos inválidos'}, status=400)

    if not id_token:
        return JsonResponse({'error': 'idToken es requerido'}, status=400)

    try:
        decoded_token = firebase_auth.verify_id_token(id_token)
        email = decoded_token['email']
        name = decoded_token.get('name', '')

        # Buscar o crear usuario
        usuario, created = Usuario.objects.get_or_create(
            email=email,
            defaults={
                'username': email.split('@')[0] + '_' + str(uuid.uuid4())[:8],  # Evitar duplicados
                'first_name': name.split(' ')[0] if name else '',
                'last_name': name.split(' ')[1] if len(name.split(' ')) > 1 else '',
                'verificado': True,  # Google ya verifica el email
            }
        )

        return JsonResponse({
            'ok': True,
            'mensaje': 'Inicio de sesión con Google exitoso',
            'usuario': {
                'id': usuario.id,
                'email': usuario.email,
                'username': usuario.username,
            }
        })

    except Exception as e:
        # DEBUG: Mostrar el error completo en consola
        print("=" * 80)
        print("ERROR EN GOOGLE LOGIN:")
        print(f"Tipo de error: {type(e).__name__}")
        print(f"Mensaje de error: {str(e)}")
        import traceback
        print("Traceback completo:")
        traceback.print_exc()
        print("=" * 80)
        return JsonResponse({'error': f'Token de Google inválido: {str(e)}'}, status=401)
@csrf_exempt
def recuperar_contrasena(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
        email = data.get('email')
        pregunta_secreta = data.get('preguntaSecreta')
        respuesta_secreta = data.get('respuestaSecreta')
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({'error': 'Datos inválidos'}, status=400)

    if not email or not pregunta_secreta or not respuesta_secreta:
        return JsonResponse({'error': 'Todos los campos son requeridos'}, status=400)

    try:
        usuario = Usuario.objects.get(email=email)
    except Usuario.DoesNotExist:
        return JsonResponse({'error': 'Usuario no encontrado'}, status=400)

    if usuario.pregunta_secreta != pregunta_secreta:
        return JsonResponse({'error': 'Pregunta secreta incorrecta'}, status=400)

    # Corregido: comparar respuesta secreta directamente (no está hasheada)
    if usuario.respuesta_secreta != respuesta_secreta:
        return JsonResponse({'error': 'Respuesta secreta incorrecta'}, status=400)

    # Generar token temporal
    temp_token = str(uuid.uuid4())
    request.session[temp_token] = {
        'email': usuario.email,
        'expira': (datetime.datetime.now() + datetime.timedelta(minutes=10)).timestamp(),
    }

    return JsonResponse({'ok': True, 'tempToken': temp_token})
@csrf_exempt
def restablecer_contrasena(request):
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
        temp_token = data.get('tempToken')
        nueva_contrasena = data.get('nuevaContrasena')
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({'error': 'Datos inválidos'}, status=400)

    if not temp_token or not nueva_contrasena:
        return JsonResponse({'error': 'tempToken y nuevaContrasena son requeridos'}, status=400)

    session_data = request.session.get(temp_token)
    if not session_data:
        return JsonResponse({'error': 'Token inválido o expirado'}, status=400)

    # Verificar expiración (10 minutos)
    if datetime.datetime.now().timestamp() > session_data['expira']:
        del request.session[temp_token]
        return JsonResponse({'error': 'Token expirado'}, status=400)

    try:
        usuario = Usuario.objects.get(email=session_data['email'])
        usuario.set_password(nueva_contrasena)
        usuario.save()
    except Usuario.DoesNotExist:
        return JsonResponse({'error': 'Usuario no encontrado'}, status=400)

    # Limpiar sesión
    del request.session[temp_token]

    return JsonResponse({'ok': True, 'mensaje': 'Contraseña actualizada con éxito'})


# ===========================
# NUEVAS VISTAS: Recuperación por Email
# ===========================

@csrf_exempt
@ratelimit(key='ip', rate='3/h', method='POST')
def solicitar_recuperacion_email(request):
    """
    Solicita recuperación de contraseña por correo electrónico
    Envía un enlace de recuperación al email del usuario
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
        email = data.get('email')
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({'error': 'Datos inválidos'}, status=400)

    if not email:
        return JsonResponse({'error': 'El email es requerido'}, status=400)

    try:
        usuario = Usuario.objects.get(email=email)
    except Usuario.DoesNotExist:
        # Por seguridad, no revelar si el email existe o no
        return JsonResponse({
            'ok': True,
            'mensaje': 'Si el correo existe, recibirás un enlace de recuperación'
        })

    # Generar token único
    token = str(uuid.uuid4())
    usuario.password_reset_token = token
    usuario.password_reset_expires = datetime.datetime.now() + datetime.timedelta(minutes=30)
    usuario.save()

    # Enviar correo
    if enviar_correo_recuperacion(usuario.email, token):
        logger.info(f"Correo de recuperación enviado a {usuario.email}")
    else:
        logger.error(f"Error al enviar correo de recuperación a {usuario.email}")

    return JsonResponse({
        'ok': True,
        'mensaje': 'Si el correo existe, recibirás un enlace de recuperación'
    })


@csrf_exempt
def restablecer_con_token_email(request):
    """
    Restablece la contraseña usando el token enviado por email
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
        token = data.get('token')
        nueva_contrasena = data.get('nuevaContrasena')
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({'error': 'Datos inválidos'}, status=400)

    if not token or not nueva_contrasena:
        return JsonResponse({'error': 'Token y nueva contraseña son requeridos'}, status=400)

    try:
        usuario = Usuario.objects.get(password_reset_token=token)
    except Usuario.DoesNotExist:
        return JsonResponse({'error': 'Token inválido'}, status=400)

    # Verificar expiración (30 minutos)
    if datetime.datetime.now() > usuario.password_reset_expires.replace(tzinfo=None):
        usuario.password_reset_token = None
        usuario.password_reset_expires = None
        usuario.save()
        return JsonResponse({'error': 'Token expirado'}, status=400)

    # Actualizar contraseña
    usuario.set_password(nueva_contrasena)
    usuario.password_reset_token = None
    usuario.password_reset_expires = None
    usuario.save()

    logger.info(f"Contraseña restablecida para {usuario.email}")

    return JsonResponse({'ok': True, 'mensaje': 'Contraseña actualizada con éxito'})


# ===========================
# NUEVAS VISTAS: TOTP (Google Authenticator)
# ===========================

@csrf_exempt
def configurar_totp(request):
    """
    Genera el secreto TOTP y devuelve el QR code como base64
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
        email = data.get('email')
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({'error': 'Datos inválidos'}, status=400)

    if not email:
        return JsonResponse({'error': 'Email es requerido'}, status=400)

    try:
        usuario = Usuario.objects.get(email=email)
    except Usuario.DoesNotExist:
        return JsonResponse({'error': 'Usuario no encontrado'}, status=400)

    # Generar secreto TOTP
    secret = usuario.generate_totp_secret()
    uri = usuario.get_totp_uri()

    # Generar QR code
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(uri)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")

    # Convertir a base64
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    img_base64 = base64.b64encode(buffer.getvalue()).decode()

    logger.info(f"TOTP configurado para {usuario.email}")

    return JsonResponse({
        'ok': True,
        'secret': secret,
        'qrCode': f"data:image/png;base64,{img_base64}",
        'mensaje': 'Escanea el QR con tu app de autenticación'
    })


@csrf_exempt
def verificar_habilitar_totp(request):
    """
    Verifica el código TOTP y habilita TOTP para el usuario
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
        email = data.get('email')
        codigo = data.get('codigo')
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({'error': 'Datos inválidos'}, status=400)

    if not email or not codigo:
        return JsonResponse({'error': 'Email y código son requeridos'}, status=400)

    try:
        usuario = Usuario.objects.get(email=email)
    except Usuario.DoesNotExist:
        return JsonResponse({'error': 'Usuario no encontrado'}, status=400)

    if usuario.verify_totp(codigo):
        usuario.totp_enabled = True
        usuario.save()
        logger.info(f"TOTP habilitado para {usuario.email}")
        return JsonResponse({'ok': True, 'mensaje': 'TOTP habilitado exitosamente'})
    else:
        return JsonResponse({'error': 'Código TOTP incorrecto'}, status=400)


@csrf_exempt
def verificar_totp_login(request):
    """
    Verifica código TOTP durante el login
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
        temp_token = data.get('tempToken')
        codigo = data.get('codigo')
        tipo = data.get('tipo', 'totp')  # 'totp' o 'backup'
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({'error': 'Datos inválidos'}, status=400)

    if not temp_token or not codigo:
        return JsonResponse({'error': 'tempToken y código son requeridos'}, status=400)

    # Obtener datos de la sesión
    session_data = request.session.get(temp_token)
    if not session_data:
        return JsonResponse({'error': 'Sesión inválida'}, status=400)

    try:
        usuario = Usuario.objects.get(email=session_data['email'])
    except Usuario.DoesNotExist:
        return JsonResponse({'error': 'Usuario no encontrado'}, status=400)

    # Verificar según el tipo
    if tipo == 'totp':
        if not usuario.totp_enabled:
            return JsonResponse({'error': 'TOTP no está habilitado'}, status=400)

        if not usuario.verify_totp(codigo):
            return JsonResponse({'error': 'Código TOTP incorrecto'}, status=400)

    elif tipo == 'backup':
        if not usuario.verify_backup_code(codigo):
            return JsonResponse({'error': 'Código de respaldo incorrecto o ya usado'}, status=400)
    else:
        return JsonResponse({'error': 'Tipo de código inválido'}, status=400)

    # Limpiar sesión
    del request.session[temp_token]

    logger.info(f"Login exitoso con {tipo} para {usuario.email}")

    return JsonResponse({
        'ok': True,
        'mensaje': 'Verificación exitosa',
        'usuario': {
            'id': usuario.id,
            'email': usuario.email,
            'username': usuario.username,
        }
    })


# ===========================
# NUEVAS VISTAS: Códigos de Respaldo
# ===========================

@csrf_exempt
def generar_codigos_respaldo(request):
    """
    Genera nuevos códigos de respaldo para el usuario
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
        email = data.get('email')
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({'error': 'Datos inválidos'}, status=400)

    if not email:
        return JsonResponse({'error': 'Email es requerido'}, status=400)

    try:
        usuario = Usuario.objects.get(email=email)
    except Usuario.DoesNotExist:
        return JsonResponse({'error': 'Usuario no encontrado'}, status=400)

    # Generar códigos
    codigos = usuario.generate_backup_codes()

    logger.info(f"Códigos de respaldo generados para {usuario.email}")

    return JsonResponse({
        'ok': True,
        'codigos': codigos,
        'mensaje': 'Guarda estos códigos en un lugar seguro. Solo se mostrarán una vez.'
    })


@csrf_exempt
def verificar_estado_seguridad(request):
    """
    Verifica el estado de seguridad del usuario (qué métodos tiene habilitados)
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
        email = data.get('email')
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({'error': 'Datos inválidos'}, status=400)

    if not email:
        return JsonResponse({'error': 'Email es requerido'}, status=400)

    try:
        usuario = Usuario.objects.get(email=email)
    except Usuario.DoesNotExist:
        return JsonResponse({'error': 'Usuario no encontrado'}, status=400)

    # Contar códigos de respaldo disponibles
    backup_codes_count = 0
    if usuario.backup_codes:
        backup_codes_count = len(usuario.backup_codes.split('|'))

    return JsonResponse({
        'ok': True,
        'email_2fa': True,  # Siempre disponible
        'totp_enabled': usuario.totp_enabled,
        'backup_codes_available': backup_codes_count,
        'security_questions': bool(usuario.pregunta_secreta and usuario.respuesta_secreta),
        'verificado': usuario.verificado,
    })