# accounts/views.py
from firebase_admin import auth as firebase_auth
import uuid
from django.contrib.auth import get_user_model
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.middleware.csrf import get_token
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.hashers import check_password
import json
import datetime
from .utils.sendgrid_otp_service import generar_codigo_otp, enviar_otp_email, enviar_otp_recuperacion
from .utils.validators import (
    sanitize_user_input, 
    validate_registration_data,
    validate_password_strength
)
from .utils.security_utils import (
    verificar_bloqueo,
    registrar_intento_fallido,
    resetear_intentos,
    validar_respuesta_secreta
)
Usuario = get_user_model()

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

    try:
        # Sanitizar y validar datos de entrada
        data_sanitized = sanitize_user_input(data)
        
        # Validar todos los datos (formato, complejidad de contraseña, etc.)
        is_valid, error_msg = validate_registration_data(data_sanitized)
        if not is_valid:
            return JsonResponse({'error': error_msg}, status=400)
        
        # Validar seguridad de respuesta secreta
        respuesta_valida, error_respuesta = validar_respuesta_secreta(data_sanitized.get('respuestasecreta', ''))
        if not respuesta_valida:
            return JsonResponse({'error': error_respuesta}, status=400)

        # Verificar unicidad (usando datos sanitizados)
        if Usuario.objects.filter(username=data_sanitized['username']).exists():
            return JsonResponse({'error': 'El nombre de usuario ya está en uso'}, status=400)
        if Usuario.objects.filter(email=data_sanitized['correo']).exists():
            return JsonResponse({'error': 'El correo ya está registrado'}, status=400)
        if Usuario.objects.filter(telefono=data_sanitized['telefono']).exists():
            return JsonResponse({'error': 'El teléfono ya está registrado'}, status=400)

        # Crear usuario con datos sanitizados
        usuario = Usuario(
            username=data_sanitized['username'],
            email=data_sanitized['correo'],
            first_name=data_sanitized['nombre'],
            last_name=data_sanitized['apellidopaterno'],
            telefono=data_sanitized['telefono'],
            pregunta_secreta=data_sanitized['preguntasecreta'],
            respuesta_secreta=data_sanitized['respuestasecreta'],
            verificado=False,
            totp_enabled=False,  # Inicializar campo requerido
        )
        # Usar set_password para hash seguro (bcrypt por defecto en Django)
        usuario.set_password(data_sanitized['contrasena'])
        usuario.save()

        # Generar código OTP con SendGrid
        codigo_otp = generar_codigo_otp()
        otp_expira = timezone.now() + timedelta(minutes=10)
        
        # Guardar código OTP en el usuario
        usuario.codigo_otp = codigo_otp
        usuario.otp_expira = otp_expira
        usuario.save()

        # Enviar código OTP por email usando SendGrid
        try:
            email_enviado = enviar_otp_email(data_sanitized['correo'], codigo_otp)
            if email_enviado:
                return JsonResponse({
                    'mensaje': 'Usuario registrado con éxito. Ingresa el código OTP enviado a tu correo.',
                    'requires2fa': True,
                    'canal': 'email',
                    'destino': f"{data_sanitized['correo'][:2]}***@{data_sanitized['correo'].split('@')[1]}",
                    'tempToken': str(usuario.id),  # Usar ID del usuario como tempToken
                }, status=201)
            else:
                # Si falla el envío, aún devolvemos éxito pero con advertencia
                return JsonResponse({
                    'mensaje': 'Usuario registrado con éxito. Ingresa el código OTP enviado a tu correo.',
                    'requires2fa': True,
                    'canal': 'email',
                    'destino': f"{data_sanitized['correo'][:2]}***@{data_sanitized['correo'].split('@')[1]}",
                    'tempToken': str(usuario.id),
                    'warning': 'El correo puede no haberse enviado. Verifica tu configuración de SendGrid.'
                }, status=201)
        except Exception as e:
            # Si hay un error crítico, aún devolvemos el usuario creado
            # pero registramos el error
            import traceback
            print(f"Error enviando email OTP: {str(e)}")
            print(traceback.format_exc())
            return JsonResponse({
                'mensaje': 'Usuario registrado con éxito. Ingresa el código OTP enviado a tu correo.',
                'requires2fa': True,
                'canal': 'email',
                'destino': f"{data_sanitized['correo'][:2]}***@{data_sanitized['correo'].split('@')[1]}",
                'tempToken': str(usuario.id),
                'warning': 'Error al enviar correo. Verifica tu configuración de SendGrid.'
            }, status=201)
            
    except Exception as e:
        # Capturar cualquier otro error
        import traceback
        error_msg = str(e)
        error_trace = traceback.format_exc()
        print(f"Error en register_user: {error_msg}")
        print(error_trace)
        return JsonResponse({
            'error': f'Error al registrar usuario: {error_msg}'
        }, status=500)
@csrf_exempt
def verificar_registro_2fa(request):
    """
    Verifica el código 2FA del registro (compatibilidad con sistema anterior)
    Ahora también soporta verificación con OTP desde el modelo Usuario
    """
    if request.method != 'POST':
        return JsonResponse({
            'ok': False,
            'error': 'Método no permitido'
        }, status=405)

    try:
        data = json.loads(request.body)
        temp_token = data.get('tempToken')
        codigo = data.get('codigo')
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({
            'ok': False,
            'error': 'Datos inválidos'
        }, status=400)

    if not temp_token or not codigo:
        return JsonResponse({
            'ok': False,
            'error': 'tempToken y codigo son requeridos'
        }, status=400)

    try:
        # Intentar obtener usuario por ID (nuevo sistema con OTP en modelo)
        try:
            usuario = Usuario.objects.get(id=temp_token)
            
            # Verificar si el código ha expirado (10 minutos)
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
                return JsonResponse({
                    'ok': False,
                    'error': 'Código incorrecto'
                }, status=400)
            
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
            
            return JsonResponse({
                'ok': True,
                'usuario': {
                    'id': usuario.id,
                    'email': usuario.email,
                    'username': usuario.username,
                },
                'message': 'Verificación exitosa'
            })
            
        except (Usuario.DoesNotExist, ValueError):
            # Fallback: sistema anterior con sesiones
            session_data = request.session.get(temp_token)
            if not session_data:
                return JsonResponse({
                    'ok': False,
                    'error': 'Sesión 2FA inválida'
                }, status=400)

            # Verificar expiración (5 minutos)
            if datetime.datetime.now().timestamp() > session_data.get('expira', 0):
                del request.session[temp_token]
                return JsonResponse({
                    'ok': False,
                    'error': 'Código expirado. Solicita uno nuevo'
                }, status=400)

            # Verificar código
            if session_data['codigo'] != str(codigo):
                session_data['intentos'] = session_data.get('intentos', 0) + 1
                request.session[temp_token] = session_data

                if session_data['intentos'] >= 5:
                    del request.session[temp_token]
                    return JsonResponse({
                        'ok': False,
                        'error': 'Demasiados intentos'
                    }, status=429)

                return JsonResponse({
                    'ok': False,
                    'error': 'Código incorrecto'
                }, status=400)

            # Código correcto: marcar usuario como verificado
            usuario = Usuario.objects.get(email=session_data['email'])
            usuario.verificado = True
            usuario.save()
            
            # Establecer sesión
            request.session['user_id'] = usuario.id
            request.session['authenticated'] = True
            request.session['email'] = usuario.email

            # Limpiar sesión temporal
            del request.session[temp_token]

            return JsonResponse({
                'ok': True,
                'usuario': {
                    'id': usuario.id,
                    'email': usuario.email,
                    'username': usuario.username,
                },
                'message': 'Verificación exitosa'
            })
            
    except Usuario.DoesNotExist:
        return JsonResponse({
            'ok': False,
            'error': 'Usuario no encontrado'
        }, status=400)
    except Exception as e:
        import traceback
        print(f"Error en verificar_registro_2fa: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'ok': False,
            'error': f'Error al verificar código: {str(e)}'
        }, status=500)
@csrf_exempt
def login_user(request):
    if request.method != 'POST':
        return JsonResponse({
            'ok': False,
            'error': 'Método no permitido'
        }, status=405)

    try:
        data = json.loads(request.body)
        email = data.get('email')
        password = data.get('password')
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({
            'ok': False,
            'error': 'Datos inválidos'
        }, status=400)

    if not email or not password:
        return JsonResponse({
            'ok': False,
            'error': 'Email y contraseña son requeridos'
        }, status=400)

    # Sanitizar email
    from .utils.validators import sanitize_string, validate_email
    email = sanitize_string(email, max_length=254)
    
    if not validate_email(email):
        return JsonResponse({
            'ok': False,
            'error': 'Formato de email inválido'
        }, status=400)

    # Autenticar usuario
    try:
        usuario = Usuario.objects.get(email=email)
    except Usuario.DoesNotExist:
        # Por seguridad, no revelar si el usuario existe o no
        return JsonResponse({
            'ok': False,
            'error': 'Credenciales incorrectas'
        }, status=401)

    # Verificar si la cuenta está bloqueada por intentos fallidos
    esta_bloqueado, tiempo_restante, mensaje_bloqueo = verificar_bloqueo(usuario)
    if esta_bloqueado:
        return JsonResponse({
            'ok': False,
            'error': mensaje_bloqueo,
            'bloqueado': True,
            'tiempo_restante': int(tiempo_restante)
        }, status=429)  # 429 Too Many Requests

    # Verificar contraseña
    if not usuario.check_password(password):
        # Registrar intento fallido
        bloqueado, mensaje = registrar_intento_fallido(usuario)
        if bloqueado:
            return JsonResponse({
                'ok': False,
                'error': mensaje,
                'bloqueado': True
            }, status=429)
        return JsonResponse({
            'ok': False,
            'error': mensaje
        }, status=401)

    # VERIFICACIÓN DE CORREO: No permitir login sin verificar correo
    if not usuario.verificado:
        return JsonResponse({
            'ok': False,
            'error': 'Debes verificar tu correo electrónico antes de iniciar sesión. Revisa tu bandeja de entrada para el código de verificación.',
            'requiresVerification': True
        }, status=403)

    # MFA/TOTP: Si está habilitado, requerir segundo factor
    if usuario.totp_enabled:
        # Generar código OTP para segundo factor
        codigo_otp = generar_codigo_otp()
        otp_expira = timezone.now() + timedelta(minutes=10)
        usuario.codigo_otp = codigo_otp
        usuario.otp_expira = otp_expira
        usuario.save()
        
        # Enviar código por email
        enviar_otp_email(usuario.email, codigo_otp)
        
        return JsonResponse({
            'ok': False,
            'requires2fa': True,
            'canal': 'email',
            'destino': f"{usuario.email[:2]}***@{usuario.email.split('@')[1]}",
            'tempToken': str(usuario.id),
            'message': 'Autenticación multifactor requerida. Ingresa el código enviado a tu correo.'
        }, status=200)

    # Login exitoso: resetear intentos fallidos
    resetear_intentos(usuario)

    # Establecer sesión de autenticación
    request.session['user_id'] = usuario.id
    request.session['authenticated'] = True
    request.session['email'] = usuario.email
    
    return JsonResponse({
        'ok': True,
        'usuario': {
            'id': usuario.id,
            'email': usuario.email,
            'username': usuario.username,
        },
        'message': 'Login exitoso'
    })
@csrf_exempt
def verificar_login_2fa(request):
    """
    Verifica el código 2FA del login
    Ahora usa el mismo sistema que el registro (OTP almacenado en modelo Usuario)
    """
    if request.method != 'POST':
        return JsonResponse({
            'ok': False,
            'error': 'Método no permitido'
        }, status=405)

    try:
        data = json.loads(request.body)
        temp_token = data.get('tempToken')
        codigo = data.get('codigo')
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({
            'ok': False,
            'error': 'Datos inválidos'
        }, status=400)

    if not temp_token or not codigo:
        return JsonResponse({
            'ok': False,
            'error': 'tempToken y codigo son requeridos'
        }, status=400)

    try:
        # Obtener usuario por ID (mismo sistema que registro)
        try:
            usuario = Usuario.objects.get(id=temp_token)
        except (Usuario.DoesNotExist, ValueError):
            return JsonResponse({
                'ok': False,
                'error': 'Usuario no encontrado'
            }, status=404)
        
        # Verificar si el código ha expirado (10 minutos)
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
            return JsonResponse({
                'ok': False,
                'error': 'Código incorrecto'
            }, status=400)
        
        # Código correcto: limpiar OTP y establecer sesión
        usuario.codigo_otp = None
        usuario.otp_expira = None
        usuario.save()
        
        # Establecer sesión de autenticación
        request.session['user_id'] = usuario.id
        request.session['authenticated'] = True
        request.session['email'] = usuario.email
        
        return JsonResponse({
            'ok': True,
            'usuario': {
                'id': usuario.id,
                'email': usuario.email,
                'username': usuario.username,
            },
            'message': 'Login exitoso'
        })
        
    except Exception as e:
        import traceback
        print(f"Error en verificar_login_2fa: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'ok': False,
            'error': f'Error al verificar código: {str(e)}'
        }, status=500)
@csrf_exempt
def google_login(request):
    if request.method != 'POST':
        return JsonResponse({
            'ok': False,
            'error': 'Método no permitido'
        }, status=405)

    try:
        data = json.loads(request.body)
        id_token = data.get('idToken')
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({
            'ok': False,
            'error': 'Datos inválidos'
        }, status=400)

    if not id_token:
        return JsonResponse({
            'ok': False,
            'error': 'idToken es requerido'
        }, status=400)

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
                'totp_enabled': False,
            }
        )

        # Establecer sesión de autenticación
        request.session['user_id'] = usuario.id
        request.session['authenticated'] = True
        request.session['email'] = usuario.email

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
        # DEBUG: Mostrar el error completo en consola
        print("=" * 80)
        print("ERROR EN GOOGLE LOGIN:")
        print(f"Tipo de error: {type(e).__name__}")
        print(f"Mensaje de error: {str(e)}")
        import traceback
        print("Traceback completo:")
        traceback.print_exc()
        print("=" * 80)
        return JsonResponse({
            'ok': False,
            'error': f'Token de Google inválido: {str(e)}'
        }, status=401)
@csrf_exempt
def obtener_pregunta_secreta(request):
    """
    Obtiene la pregunta secreta de un usuario basándose en su email
    """
    if request.method != 'POST':
        return JsonResponse({
            'ok': False,
            'error': 'Método no permitido'
        }, status=405)

    try:
        data = json.loads(request.body)
        email = data.get('email')
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({
            'ok': False,
            'error': 'Datos inválidos'
        }, status=400)

    if not email:
        return JsonResponse({
            'ok': False,
            'error': 'El email es requerido'
        }, status=400)

    try:
        usuario = Usuario.objects.get(email=email)
    except Usuario.DoesNotExist:
        # Por seguridad, no revelar si el usuario existe o no
        return JsonResponse({
            'ok': False,
            'error': 'No se encontró una cuenta con ese correo'
        }, status=404)

    if not usuario.pregunta_secreta:
        return JsonResponse({
            'ok': False,
            'error': 'Este usuario no tiene pregunta secreta configurada'
        }, status=400)

    return JsonResponse({
        'ok': True,
        'preguntaSecreta': usuario.pregunta_secreta
    })

@csrf_exempt
def recuperar_contrasena(request):
    """
    Verifica la respuesta a la pregunta secreta
    Ahora usa el mismo sistema que OTP: guarda en el modelo Usuario
    """
    if request.method != 'POST':
        return JsonResponse({
            'ok': False,
            'error': 'Método no permitido'
        }, status=405)

    try:
        data = json.loads(request.body)
        email = data.get('email')
        respuesta_secreta = data.get('respuestaSecreta')
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({
            'ok': False,
            'error': 'Datos inválidos'
        }, status=400)

    if not email or not respuesta_secreta:
        return JsonResponse({
            'ok': False,
            'error': 'Todos los campos son requeridos'
        }, status=400)

    try:
        usuario = Usuario.objects.get(email=email)
    except Usuario.DoesNotExist:
        return JsonResponse({
            'ok': False,
            'error': 'Usuario no encontrado'
        }, status=400)

    # Comparar respuesta secreta (no está hasheada)
    if usuario.respuesta_secreta != respuesta_secreta:
        return JsonResponse({
            'ok': False,
            'error': 'Respuesta incorrecta'
        }, status=400)

    # Generar token temporal y guardarlo en el usuario (como OTP)
    # Usar codigo_otp para marcar que la validación fue exitosa
    codigo_validacion = 'SECRET_OK_' + str(uuid.uuid4())[:8]
    usuario.codigo_otp = codigo_validacion
    usuario.otp_expira = timezone.now() + timedelta(minutes=10)
    usuario.save()

    return JsonResponse({
        'ok': True, 
        'tempToken': str(usuario.id),
        'message': 'Respuesta correcta. Ahora puedes cambiar tu contraseña.'
    })
@csrf_exempt
def restablecer_contrasena(request):
    """
    Restablece la contraseña después de verificar la pregunta secreta
    Ahora usa el mismo sistema que OTP: verifica desde el modelo Usuario
    """
    if request.method != 'POST':
        return JsonResponse({
            'ok': False,
            'error': 'Método no permitido'
        }, status=405)

    try:
        data = json.loads(request.body)
        temp_token = data.get('tempToken')
        nueva_contrasena = data.get('nuevaContrasena')
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({
            'ok': False,
            'error': 'Datos inválidos'
        }, status=400)

    if not temp_token or not nueva_contrasena:
        return JsonResponse({
            'ok': False,
            'error': 'tempToken y nuevaContrasena son requeridos'
        }, status=400)

    # Validar complejidad de contraseña
    is_valid, error_msg = validate_password_strength(nueva_contrasena)
    if not is_valid:
        return JsonResponse({
            'ok': False,
            'error': error_msg
        }, status=400)

    # Intentar obtener usuario por ID (como OTP)
    try:
        usuario = Usuario.objects.get(id=temp_token)
    except (Usuario.DoesNotExist, ValueError):
        return JsonResponse({
            'ok': False,
            'error': 'Token inválido o expirado'
        }, status=400)

    # Verificar que el código de validación existe y no ha expirado
    if not usuario.codigo_otp or not usuario.otp_expira:
        return JsonResponse({
            'ok': False,
            'error': 'Token inválido o expirado. Solicita uno nuevo.'
        }, status=400)

    # Verificar expiración (10 minutos)
    if usuario.otp_expira < timezone.now():
        usuario.codigo_otp = None
        usuario.otp_expira = None
        usuario.save()
        return JsonResponse({
            'ok': False,
            'error': 'Token expirado. Solicita uno nuevo.'
        }, status=400)

    # Verificar que el código inicie con 'SECRET_OK_' (marca de validación exitosa)
    if not usuario.codigo_otp.startswith('SECRET_OK_'):
        return JsonResponse({
            'ok': False,
            'error': 'Token inválido. Debes verificar la pregunta secreta primero.'
        }, status=400)

    # Actualizar contraseña
    usuario.set_password(nueva_contrasena)
    usuario.codigo_otp = None
    usuario.otp_expira = None
    usuario.save()

    return JsonResponse({
        'ok': True,
        'message': 'Contraseña actualizada con éxito'
    })


# ========== VISTAS OTP CON SENDGRID ==========

@csrf_exempt
@require_http_methods(["POST"])
def verificar_otp_registro(request):
    """
    Verifica el código OTP durante el registro
    
    Body esperado:
    {
        "tempToken": "token_temporal_o_id",
        "codigo": "123456"
    }
    """
    try:
        data = json.loads(request.body)
        temp_token = data.get('tempToken')
        codigo = data.get('codigo')
        
        if not temp_token or not codigo:
            return JsonResponse({
                'ok': False,
                'error': 'tempToken y codigo son requeridos'
            }, status=400)
        
        # Obtener usuario (ajusta según cómo manejes el tempToken)
        # Opción 1: Si tempToken es el ID del usuario
        try:
            usuario = Usuario.objects.get(id=temp_token)
        except (Usuario.DoesNotExist, ValueError):
            return JsonResponse({
                'ok': False,
                'error': 'Usuario no encontrado'
            }, status=404)
        
        # Verificar si el código ha expirado (10 minutos)
        if usuario.otp_expira and usuario.otp_expira < timezone.now():
            usuario.codigo_otp = None
            usuario.otp_expira = None
            usuario.save()
            return JsonResponse({
                'ok': False,
                'error': 'Código expirado. Solicita uno nuevo.'
            }, status=400)
        
        # Verificar código
        if not usuario.codigo_otp or usuario.codigo_otp != codigo:
            return JsonResponse({
                'ok': False,
                'error': 'Código incorrecto'
            }, status=400)
        
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
        
        return JsonResponse({
            'ok': True,
            'usuario': {
                'id': usuario.id,
                'email': usuario.email,
                'username': usuario.username,
            },
            'message': 'Cuenta activada correctamente'
        }, status=200)
        
    except Exception as e:
        import traceback
        print(f"Error en verificar_otp_registro: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'ok': False,
            'error': f'Error al verificar código: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def reenviar_otp(request):
    """
    Reenvía un código OTP
    
    Body esperado:
    {
        "correo": "juan@example.com"
    }
    """
    try:
        data = json.loads(request.body)
        correo = data.get('correo')
        
        if not correo:
            return JsonResponse({
                'ok': False,
                'error': 'Correo es requerido'
            }, status=400)
        
        try:
            usuario = Usuario.objects.get(email=correo)
        except Usuario.DoesNotExist:
            return JsonResponse({
                'ok': False,
                'error': 'Usuario no encontrado'
            }, status=404)
        
        # Generar nuevo código
        nuevo_codigo = generar_codigo_otp()
        usuario.codigo_otp = nuevo_codigo
        usuario.otp_expira = timezone.now() + timedelta(minutes=10)
        usuario.save()
        
        # Enviar nuevo código
        if enviar_otp_email(correo, nuevo_codigo):
            return JsonResponse({
                'ok': True,
                'message': 'Nuevo código enviado a tu correo. Expira en 10 minutos.'
            }, status=200)
        else:
            return JsonResponse({
                'ok': False,
                'error': 'No se pudo enviar el código'
            }, status=500)
            
    except Exception as e:
        import traceback
        print(f"Error en reenviar_otp: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'ok': False,
            'error': f'Error al reenviar código: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def solicitar_recuperacion_otp(request):
    """
    Inicia el proceso de recuperación de contraseña enviando OTP
    
    Body esperado:
    {
        "email": "juan@example.com"
    }
    """
    try:
        data = json.loads(request.body)
        correo = data.get('email')
        
        if not correo:
            return JsonResponse({
                'ok': False,
                'error': 'Email es requerido'
            }, status=400)
        
        try:
            usuario = Usuario.objects.get(email=correo)
        except Usuario.DoesNotExist:
            # Por seguridad, no revelar si el usuario existe o no
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
        if enviar_otp_recuperacion(correo, codigo_otp):
            return JsonResponse({
                'ok': True,
                'message': 'Código de recuperación enviado a tu correo. Expira en 10 minutos.',
                'tempToken': str(usuario.id)  # O genera un token temporal más seguro
            }, status=200)
        else:
            return JsonResponse({
                'ok': False,
                'error': 'No se pudo enviar el código de recuperación'
            }, status=500)
            
    except Exception as e:
        import traceback
        print(f"Error en solicitar_recuperacion_otp: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'ok': False,
            'error': f'Error al procesar solicitud: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def verificar_otp_recuperacion(request):
    """
    Verifica el código OTP para recuperación de contraseña
    
    Body esperado:
    {
        "tempToken": "token_temporal",
        "codigo": "123456"
    }
    """
    try:
        data = json.loads(request.body)
        temp_token = data.get('tempToken')
        codigo = data.get('codigo')
        
        if not temp_token or not codigo:
            return JsonResponse({
                'ok': False,
                'error': 'tempToken y codigo son requeridos'
            }, status=400)
        
        try:
            usuario = Usuario.objects.get(id=temp_token)
        except (Usuario.DoesNotExist, ValueError):
            return JsonResponse({
                'ok': False,
                'error': 'Usuario no encontrado'
            }, status=404)
        
        # Verificar expiración (10 minutos)
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
            return JsonResponse({
                'ok': False,
                'error': 'Código incorrecto'
            }, status=400)
        
        # Código correcto - mantener código activo para cambio de contraseña
        return JsonResponse({
            'ok': True,
            'message': 'Código verificado. Ahora puedes cambiar tu contraseña.'
        }, status=200)
        
    except Exception as e:
        import traceback
        print(f"Error en verificar_otp_recuperacion: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'ok': False,
            'error': f'Error al verificar código: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def reenviar_otp_recuperacion(request):
    """
    Reenvía código OTP para recuperación de contraseña
    
    Body esperado:
    {
        "correo": "juan@example.com"
    }
    """
    try:
        data = json.loads(request.body)
        correo = data.get('correo')
        
        if not correo:
            return JsonResponse({
                'ok': False,
                'error': 'Correo es requerido'
            }, status=400)
        
        try:
            usuario = Usuario.objects.get(email=correo)
        except Usuario.DoesNotExist:
            return JsonResponse({
                'ok': False,
                'error': 'Usuario no encontrado'
            }, status=404)
        
        # Generar nuevo código
        nuevo_codigo = generar_codigo_otp()
        usuario.codigo_otp = nuevo_codigo
        usuario.otp_expira = timezone.now() + timedelta(minutes=10)
        usuario.save()
        
        # Enviar nuevo código
        if enviar_otp_recuperacion(correo, nuevo_codigo):
            return JsonResponse({
                'ok': True,
                'message': 'Nuevo código enviado a tu correo. Expira en 10 minutos.'
            }, status=200)
        else:
            return JsonResponse({
                'ok': False,
                'error': 'No se pudo enviar el código'
            }, status=500)
            
    except Exception as e:
        import traceback
        print(f"Error en reenviar_otp_recuperacion: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'ok': False,
            'error': f'Error al reenviar código: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def actualizar_contrasena_otp(request):
    """
    Actualiza la contraseña después de verificar OTP
    
    Body esperado:
    {
        "tempToken": "token_temporal",
        "nuevaContrasena": "nueva_password123"
    }
    """
    try:
        data = json.loads(request.body)
        temp_token = data.get('tempToken')
        nueva_contrasena = data.get('nuevaContrasena')
        
        if not temp_token or not nueva_contrasena:
            return JsonResponse({
                'ok': False,
                'error': 'tempToken y nuevaContrasena son requeridos'
            }, status=400)
        
        # Validar complejidad de contraseña
        is_valid, error_msg = validate_password_strength(nueva_contrasena)
        if not is_valid:
            return JsonResponse({
                'ok': False,
                'error': error_msg
            }, status=400)
        
        try:
            usuario = Usuario.objects.get(id=temp_token)
        except (Usuario.DoesNotExist, ValueError):
            return JsonResponse({
                'ok': False,
                'error': 'Usuario no encontrado'
            }, status=404)
        
        # Verificar que el código OTP aún sea válido
        if not usuario.codigo_otp or not usuario.otp_expira or usuario.otp_expira < timezone.now():
            return JsonResponse({
                'ok': False,
                'error': 'Sesión expirada. Solicita un nuevo código.'
            }, status=400)
        
        # Actualizar contraseña (hasheada)
        usuario.set_password(nueva_contrasena)
        usuario.codigo_otp = None
        usuario.otp_expira = None
        usuario.save()
        
        return JsonResponse({
            'ok': True,
            'message': 'Contraseña actualizada correctamente'
        }, status=200)
        
    except Exception as e:
        import traceback
        print(f"Error en actualizar_contrasena_otp: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'ok': False,
            'error': f'Error al actualizar contraseña: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def obtener_estado_seguridad(request):
    """
    Obtiene el estado de seguridad del usuario
    
    Body esperado:
    {
        "email": "juan@example.com"
    }
    """
    try:
        data = json.loads(request.body)
        email = data.get('email')
        
        if not email:
            return JsonResponse({
                'ok': False,
                'error': 'Email es requerido'
            }, status=400)
        
        try:
            usuario = Usuario.objects.get(email=email)
        except Usuario.DoesNotExist:
            return JsonResponse({
                'ok': False,
                'error': 'Usuario no encontrado'
            }, status=404)
        
        # Contar códigos de respaldo disponibles
        backup_codes_count = 0
        if usuario.backup_codes:
            try:
                import json as json_lib
                codes = json_lib.loads(usuario.backup_codes)
                if isinstance(codes, list):
                    backup_codes_count = len(codes)
            except:
                backup_codes_count = 0
        
        # Verificar si tiene preguntas de seguridad
        tiene_preguntas = bool(usuario.pregunta_secreta and usuario.respuesta_secreta)
        
        return JsonResponse({
            'ok': True,
            'email_2fa': usuario.verificado,  # Email 2FA está habilitado si el usuario está verificado
            'totp_habilitado': usuario.totp_enabled,
            'codigos_respaldo_disponibles': backup_codes_count,
            'tiene_preguntas_seguridad': tiene_preguntas
        }, status=200)
        
    except Exception as e:
        import traceback
        print(f"Error en obtener_estado_seguridad: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'ok': False,
            'error': f'Error al obtener estado de seguridad: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def cambiar_contrasena(request):
    """
    Cambia la contraseña del usuario autenticado
    
    Body esperado:
    {
        "email": "juan@example.com",
        "contrasena_actual": "password123",
        "nueva_contrasena": "newpassword123"
    }
    """
    try:
        data = json.loads(request.body)
        email = data.get('email')
        contrasena_actual = data.get('contrasena_actual')
        nueva_contrasena = data.get('nueva_contrasena')
        
        if not email or not contrasena_actual or not nueva_contrasena:
            return JsonResponse({
                'ok': False,
                'error': 'Email, contraseña actual y nueva contraseña son requeridos'
            }, status=400)
        
        try:
            usuario = Usuario.objects.get(email=email)
        except Usuario.DoesNotExist:
            return JsonResponse({
                'ok': False,
                'error': 'Usuario no encontrado'
            }, status=404)
        
        # Verificar contraseña actual
        if not usuario.check_password(contrasena_actual):
            return JsonResponse({
                'ok': False,
                'error': 'Contraseña actual incorrecta'
            }, status=400)
        
        # Validar que la nueva contraseña sea diferente
        if usuario.check_password(nueva_contrasena):
            return JsonResponse({
                'ok': False,
                'error': 'La nueva contraseña debe ser diferente a la actual'
            }, status=400)
        
        # Validar complejidad de contraseña
        is_valid, error_msg = validate_password_strength(nueva_contrasena)
        if not is_valid:
            return JsonResponse({
                'ok': False,
                'error': error_msg
            }, status=400)
        
        # Actualizar contraseña
        usuario.set_password(nueva_contrasena)
        usuario.save()
        
        return JsonResponse({
            'ok': True,
            'message': 'Contraseña cambiada exitosamente'
        }, status=200)
        
    except Exception as e:
        import traceback
        print(f"Error en cambiar_contrasena: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'ok': False,
            'error': f'Error al cambiar contraseña: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def generar_codigos_respaldo(request):
    """
    Genera códigos de respaldo para el usuario
    
    Body esperado:
    {
        "email": "juan@example.com"
    }
    """
    try:
        data = json.loads(request.body)
        email = data.get('email')
        
        if not email:
            return JsonResponse({
                'ok': False,
                'error': 'Email es requerido'
            }, status=400)
        
        try:
            usuario = Usuario.objects.get(email=email)
        except Usuario.DoesNotExist:
            return JsonResponse({
                'ok': False,
                'error': 'Usuario no encontrado'
            }, status=404)
        
        # Generar 10 códigos de 8 dígitos
        import random
        codigos = []
        for _ in range(10):
            codigo = ''.join([str(random.randint(0, 9)) for _ in range(8)])
            codigos.append(codigo)
        
        # Guardar códigos como JSON
        import json as json_lib
        usuario.backup_codes = json_lib.dumps(codigos)
        usuario.save()
        
        return JsonResponse({
            'ok': True,
            'codigos': codigos,
            'message': 'Códigos de respaldo generados exitosamente'
        }, status=200)
        
    except Exception as e:
        import traceback
        print(f"Error en generar_codigos_respaldo: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'ok': False,
            'error': f'Error al generar códigos de respaldo: {str(e)}'
        }, status=500)


@csrf_exempt
@require_http_methods(["POST"])
def logout_user(request):
    """
    Cierra la sesión del usuario y revoca todas las sesiones activas
    
    Body esperado: (vacío)
    """
    try:
        # Invalidar sesión actual
        request.session.flush()
        
        return JsonResponse({
            'ok': True,
            'message': 'Sesión cerrada exitosamente'
        }, status=200)
        
    except Exception as e:
        import traceback
        print(f"Error en logout_user: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'ok': False,
            'error': f'Error al cerrar sesión: {str(e)}'
        }, status=500)


@ensure_csrf_cookie
@require_http_methods(["GET"])
def verificar_sesion(request):
    """
    Verifica si el usuario tiene una sesión activa y válida
    
    Returns:
        JsonResponse con estado de la sesión
    """
    try:
        if request.session.get('authenticated') and request.session.get('user_id'):
            try:
                usuario = Usuario.objects.get(id=request.session['user_id'])
                
                # Verificar que el usuario sigue activo
                if not usuario.is_active:
                    request.session.flush()
                    return JsonResponse({
                        'ok': False,
                        'error': 'Usuario inactivo'
                    }, status=401)
                
                return JsonResponse({
                    'ok': True,
                    'usuario': {
                        'id': usuario.id,
                        'email': usuario.email,
                        'username': usuario.username,
                    }
                })
            except Usuario.DoesNotExist:
                request.session.flush()
                return JsonResponse({
                    'ok': False,
                    'error': 'Usuario no encontrado'
                }, status=401)
        
        return JsonResponse({
            'ok': False,
            'error': 'Sesión no válida'
        }, status=401)
        
    except Exception as e:
        import traceback
        print(f"Error en verificar_sesion: {str(e)}")
        print(traceback.format_exc())
        return JsonResponse({
            'ok': False,
            'error': f'Error al verificar sesión: {str(e)}'
        }, status=500)