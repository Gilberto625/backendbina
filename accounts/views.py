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
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.hashers import make_password, check_password
import json
import datetime
from .utils.sendgrid_otp_service import generar_codigo_otp, enviar_otp_email, enviar_otp_recuperacion
Usuario = get_user_model()

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

    try:
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
            totp_enabled=False,  # Inicializar campo requerido
        )
        usuario.set_password(data['contrasena'])
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
            email_enviado = enviar_otp_email(data['correo'], codigo_otp)
            if email_enviado:
                return JsonResponse({
                    'mensaje': 'Usuario registrado con éxito. Ingresa el código OTP enviado a tu correo.',
                    'requires2fa': True,
                    'canal': 'email',
                    'destino': f"{data['correo'][:2]}***@{data['correo'].split('@')[1]}",
                    'tempToken': str(usuario.id),  # Usar ID del usuario como tempToken
                }, status=201)
            else:
                # Si falla el envío, aún devolvemos éxito pero con advertencia
                return JsonResponse({
                    'mensaje': 'Usuario registrado con éxito. Ingresa el código OTP enviado a tu correo.',
                    'requires2fa': True,
                    'canal': 'email',
                    'destino': f"{data['correo'][:2]}***@{data['correo'].split('@')[1]}",
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
                'destino': f"{data['correo'][:2]}***@{data['correo'].split('@')[1]}",
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
    except Usuario.DoesNotExist:
        return JsonResponse({'error': 'Usuario no encontrado'}, status=400)

    # Limpiar sesión
    del request.session[temp_token]

    return JsonResponse({'ok': True, 'mensaje': 'Verificación exitosa'})
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

    # Autenticar usuario
    try:
        usuario = Usuario.objects.get(email=email)
    except Usuario.DoesNotExist:
        return JsonResponse({
            'ok': False,
            'error': 'Credenciales incorrectas'
        }, status=401)

    if not usuario.check_password(password):
        return JsonResponse({
            'ok': False,
            'error': 'Credenciales incorrectas'
        }, status=401)

    # Si el usuario está verificado, requiere 2FA
    if usuario.verificado:
        codigo = generar_codigo()
        temp_token = str(uuid.uuid4())
        request.session[temp_token] = {
            'email': usuario.email,
            'codigo': codigo,
            'intentos': 0,
            'expira': (datetime.datetime.now() + datetime.timedelta(minutes=5)).timestamp()
        }

        try:
            send_mail(
                'Código de verificación',
                f'Tu código es: {codigo}. Expira en 5 minutos.',
                settings.DEFAULT_FROM_EMAIL,
                [usuario.email],
                fail_silently=False,
            )
        except Exception:
            return JsonResponse({
                'ok': False,
                'error': 'No se pudo enviar el correo'
            }, status=500)

        return JsonResponse({
            'requires2fa': True,
            'tempToken': temp_token,
            'destino': usuario.email,
            'metodos_disponibles': ['email']
        })

    # Si no está verificado, login directo sin 2FA
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

    # Obtener datos de la sesión
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
        request.session[temp_token] = session_data  # Guardar intentos

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

    # Código correcto: obtener usuario
    try:
        usuario = Usuario.objects.get(email=session_data['email'])
    except Usuario.DoesNotExist:
        return JsonResponse({
            'ok': False,
            'error': 'Usuario no encontrado'
        }, status=400)

    # Establecer sesión de autenticación
    request.session['user_id'] = usuario.id
    request.session['authenticated'] = True
    request.session['email'] = usuario.email
    
    # Limpiar sesión temporal 2FA
    del request.session[temp_token]

    # Retornar respuesta con usuario (estructura requerida por frontend)
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
                'error': 'tempToken y codigo son requeridos'
            }, status=400)
        
        # Obtener usuario (ajusta según cómo manejes el tempToken)
        # Opción 1: Si tempToken es el ID del usuario
        try:
            usuario = Usuario.objects.get(id=temp_token)
        except (Usuario.DoesNotExist, ValueError):
            return JsonResponse({
                'error': 'Usuario no encontrado'
            }, status=404)
        
        # Verificar si el código ha expirado (10 minutos)
        if usuario.otp_expira and usuario.otp_expira < timezone.now():
            usuario.codigo_otp = None
            usuario.otp_expira = None
            usuario.save()
            return JsonResponse({
                'error': 'Código expirado. Solicita uno nuevo.'
            }, status=400)
        
        # Verificar código
        if not usuario.codigo_otp or usuario.codigo_otp != codigo:
            return JsonResponse({
                'error': 'Código incorrecto'
            }, status=400)
        
        # Activar cuenta
        usuario.confirmado = True
        usuario.verificado = True
        usuario.codigo_otp = None
        usuario.otp_expira = None
        usuario.save()
        
        return JsonResponse({
            'ok': True,
            'message': 'Cuenta activada correctamente'
        }, status=200)
        
    except Exception as e:
        return JsonResponse({
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
                'error': 'Correo es requerido'
            }, status=400)
        
        try:
            usuario = Usuario.objects.get(email=correo)
        except Usuario.DoesNotExist:
            return JsonResponse({
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
                'message': 'Nuevo código enviado a tu correo. Expira en 10 minutos.'
            }, status=200)
        else:
            return JsonResponse({
                'error': 'No se pudo enviar el código'
            }, status=500)
            
    except Exception as e:
        return JsonResponse({
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
                'error': 'Email es requerido'
            }, status=400)
        
        try:
            usuario = Usuario.objects.get(email=correo)
        except Usuario.DoesNotExist:
            # Por seguridad, no revelar si el usuario existe o no
            return JsonResponse({
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
                'message': 'Código de recuperación enviado a tu correo. Expira en 10 minutos.',
                'tempToken': str(usuario.id)  # O genera un token temporal más seguro
            }, status=200)
        else:
            return JsonResponse({
                'error': 'No se pudo enviar el código de recuperación'
            }, status=500)
            
    except Exception as e:
        return JsonResponse({
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
                'error': 'tempToken y codigo son requeridos'
            }, status=400)
        
        try:
            usuario = Usuario.objects.get(id=temp_token)
        except (Usuario.DoesNotExist, ValueError):
            return JsonResponse({
                'error': 'Usuario no encontrado'
            }, status=404)
        
        # Verificar expiración (10 minutos)
        if not usuario.otp_expira or usuario.otp_expira < timezone.now():
            usuario.codigo_otp = None
            usuario.otp_expira = None
            usuario.save()
            return JsonResponse({
                'error': 'Código expirado. Solicita uno nuevo.'
            }, status=400)
        
        # Verificar código
        if not usuario.codigo_otp or usuario.codigo_otp != codigo:
            return JsonResponse({
                'error': 'Código incorrecto'
            }, status=400)
        
        # Código correcto - mantener código activo para cambio de contraseña
        return JsonResponse({
            'ok': True,
            'message': 'Código verificado. Ahora puedes cambiar tu contraseña.'
        }, status=200)
        
    except Exception as e:
        return JsonResponse({
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
                'error': 'Correo es requerido'
            }, status=400)
        
        try:
            usuario = Usuario.objects.get(email=correo)
        except Usuario.DoesNotExist:
            return JsonResponse({
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
                'message': 'Nuevo código enviado a tu correo. Expira en 10 minutos.'
            }, status=200)
        else:
            return JsonResponse({
                'error': 'No se pudo enviar el código'
            }, status=500)
            
    except Exception as e:
        return JsonResponse({
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
                'error': 'tempToken y nuevaContrasena son requeridos'
            }, status=400)
        
        if len(nueva_contrasena) < 8:
            return JsonResponse({
                'error': 'La contraseña debe tener al menos 8 caracteres'
            }, status=400)
        
        try:
            usuario = Usuario.objects.get(id=temp_token)
        except (Usuario.DoesNotExist, ValueError):
            return JsonResponse({
                'error': 'Usuario no encontrado'
            }, status=404)
        
        # Verificar que el código OTP aún sea válido
        if not usuario.codigo_otp or not usuario.otp_expira or usuario.otp_expira < timezone.now():
            return JsonResponse({
                'error': 'Sesión expirada. Solicita un nuevo código.'
            }, status=400)
        
        # Actualizar contraseña (hasheada)
        usuario.set_password(nueva_contrasena)
        usuario.codigo_otp = None
        usuario.otp_expira = None
        usuario.save()
        
        return JsonResponse({
            'message': 'Contraseña actualizada correctamente'
        }, status=200)
        
    except Exception as e:
        return JsonResponse({
            'error': f'Error al actualizar contraseña: {str(e)}'
        }, status=500)