# accounts/views.py
from firebase_admin import auth as firebase_auth
import uuid
import random
import logging
import threading
import queue
from django.contrib.auth import get_user_model
from django.core.mail import send_mail
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.middleware.csrf import get_token
import json
import datetime
from django.contrib.auth.hashers import check_password

logger = logging.getLogger(__name__)
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

    # Intentar enviar correo
    email_sent = False
    email_error = None
    email_test_mode = getattr(settings, 'EMAIL_TEST_MODE', False)
    
    logger.info(f'📧 Intentando enviar código OTP a {data["correo"]}')
    logger.info(f'📧 Configuración email: HOST={settings.EMAIL_HOST}, FROM={settings.DEFAULT_FROM_EMAIL}')
    logger.info(f'📧 Modo prueba: {email_test_mode}')
    logger.info(f'🔑 Código OTP generado: {codigo} (para pruebas/verificación manual)')
    
    # Si está en modo prueba, no intentar enviar correo real
    if email_test_mode:
        logger.warning(f'⚠️ MODO PRUEBA: No se enviará correo real. Código OTP: {codigo}')
        email_sent = False  # Marcar como no enviado para que el frontend sepa
    else:
        # Intentar enviar correo real con timeout usando threading
        try:
            import threading
            import queue
            
            result_queue = queue.Queue()
            
            def send_email_thread():
                try:
                    send_mail(
                        'Código de verificación',
                        f'Tu código es: {codigo}. Expira en 5 minutos.',
                        settings.DEFAULT_FROM_EMAIL,
                        [data['correo']],
                        fail_silently=False,
                    )
                    result_queue.put(('success', None))
                except Exception as e:
                    result_queue.put(('error', e))
            
            # Iniciar thread para enviar correo
            email_thread = threading.Thread(target=send_email_thread, daemon=True)
            email_thread.start()
            email_thread.join(timeout=10)  # Timeout de 10 segundos
            
            if email_thread.is_alive():
                logger.error(f'⏱️ Timeout: El envío de correo tomó más de 10 segundos')
                email_error = 'Timeout: El servidor de correo no respondió a tiempo'
            else:
                result_type, result_value = result_queue.get_nowait()
                if result_type == 'success':
                    email_sent = True
                    logger.info(f'✅ Correo enviado exitosamente a {data["correo"]}')
                else:
                    email_error = str(result_value)
                    logger.error(f'❌ Error al enviar correo: {email_error}')
                    
        except Exception as e:
            email_error = str(e)
            logger.error(f'❌ Error al enviar correo a {data["correo"]}: {email_error}')
            logger.error(f'❌ Tipo de error: {type(e).__name__}')
            logger.error(f'❌ Detalles completos: {repr(e)}')
    
    # Si el correo no se pudo enviar (o está en modo prueba), aún así retornar éxito
    # pero indicar que el correo no se envió
    if not email_sent:
        logger.warning(f'⚠️ Usuario creado pero correo NO enviado. Código OTP: {codigo}')
        return JsonResponse({
            'mensaje': 'Usuario registrado con éxito',
            'requires2fa': True,
            'canal': 'email',
            'destino': f"{data['correo'][:2]}***@{data['correo'].split('@')[1]}",
            'tempToken': temp_token,
            'email_enviado': False,
            'codigo_otp': codigo if email_test_mode else None,  # Solo en modo prueba mostrar código
            'advertencia': 'El correo no se pudo enviar. ' + 
                          (f'Código OTP para pruebas: {codigo}' if email_test_mode else 
                           'Contacta al administrador o revisa los logs del servidor.')
        }, status=201)

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
    except Usuario.DoesNotExist:
        return JsonResponse({'error': 'Usuario no encontrado'}, status=400)

    # Limpiar sesión
    del request.session[temp_token]

    return JsonResponse({'ok': True, 'mensaje': 'Verificación exitosa'})
@csrf_exempt
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

    # ADMIN: Login directo SIN 2FA
    # CLIENTE: Si está verificado, requiere 2FA
    if usuario.rol == 'cliente' and usuario.verificado:
        codigo = generar_codigo()
        temp_token = str(uuid.uuid4())
        request.session[temp_token] = {
            'email': usuario.email,
            'codigo': codigo,
            'intentos': 0,
            'expira': (datetime.datetime.now() + datetime.timedelta(minutes=5)).timestamp()
        }

        email_test_mode = getattr(settings, 'EMAIL_TEST_MODE', False)
        email_sent = False
        email_error = None
        
        logger.info(f'📧 Intentando enviar código OTP de login a {usuario.email}')
        logger.info(f'🔑 Código OTP generado: {codigo} (para pruebas/verificación manual)')
        
        if email_test_mode:
            logger.warning(f'⚠️ MODO PRUEBA: No se enviará correo real. Código OTP: {codigo}')
        else:
            try:
                result_queue = queue.Queue()
                
                def send_email_thread():
                    try:
                        send_mail(
                            'Código de verificación',
                            f'Tu código es: {codigo}. Expira en 5 minutos.',
                            settings.DEFAULT_FROM_EMAIL,
                            [usuario.email],
                            fail_silently=False,
                        )
                        result_queue.put(('success', None))
                    except Exception as e:
                        result_queue.put(('error', e))
                
                email_thread = threading.Thread(target=send_email_thread, daemon=True)
                email_thread.start()
                email_thread.join(timeout=10)
                
                if email_thread.is_alive():
                    logger.error(f'⏱️ Timeout: El envío de correo tomó más de 10 segundos')
                    email_error = 'Timeout: El servidor de correo no respondió a tiempo'
                else:
                    result_type, result_value = result_queue.get_nowait()
                    if result_type == 'success':
                        email_sent = True
                        logger.info(f'✅ Correo de login enviado exitosamente a {usuario.email}')
                    else:
                        email_error = str(result_value)
                        logger.error(f'❌ Error al enviar correo de login: {email_error}')
                        
            except Exception as e:
                email_error = str(e)
                logger.error(f'❌ Error al enviar correo de login a {usuario.email}: {email_error}')
        
        # Si el correo no se pudo enviar, aún así permitir continuar con el 2FA
        # El código está en la sesión, pueden verificarlo manualmente si es necesario
        if not email_sent and not email_test_mode:
            logger.warning(f'⚠️ Correo NO enviado pero continuando con 2FA. Código: {codigo}')

        return JsonResponse({
            'requires2fa': True,
            'tempToken': temp_token,
            'canal': 'email',
            'destino': f"{email[:2]}***@{email.split('@')[1]}",
        })

    # Admin o cliente no verificado: Login directo
    return JsonResponse({
        'ok': True,
        'mensaje': 'Inicio de sesión exitoso',
        'usuario': {
            'id': usuario.id,
            'email': usuario.email,
            'username': usuario.username,
            'nombre': usuario.first_name,
            'apellido': usuario.last_name,
            'rol': usuario.rol,
        }
    })
@csrf_exempt
def verificar_login_2fa(request):
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

    # Código correcto: obtener usuario
    try:
        usuario = Usuario.objects.get(email=session_data['email'])
    except Usuario.DoesNotExist:
        return JsonResponse({'error': 'Usuario no encontrado'}, status=400)

    # Limpiar sesión
    del request.session[temp_token]

    # Devolver datos del usuario con rol
    return JsonResponse({
        'ok': True,
        'mensaje': 'Inicio de sesión exitoso',
        'usuario': {
            'id': usuario.id,
            'email': usuario.email,
            'username': usuario.username,
            'nombre': usuario.first_name,
            'apellido': usuario.last_name,
            'rol': usuario.rol,
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
                'nombre': usuario.first_name,
                'apellido': usuario.last_name,
                'rol': usuario.rol,
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
def recuperar_otp(request):
    """
    Enviar código OTP por email para recuperación de contraseña
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

    # Verificar si el usuario existe
    try:
        usuario = Usuario.objects.get(email=email)
    except Usuario.DoesNotExist:
        # Por seguridad, no revelamos si el email existe o no
        return JsonResponse({
            'ok': True,
            'mensaje': 'Si el correo existe, se enviará un código de recuperación.'
        })

    # Generar código OTP
    codigo = generar_codigo()
    temp_token = str(uuid.uuid4())
    request.session[temp_token] = {
        'email': usuario.email,
        'codigo': codigo,
        'tipo': 'recuperacion',
        'intentos': 0,
        'expira': (datetime.datetime.now() + datetime.timedelta(minutes=10)).timestamp()
    }

    email_test_mode = getattr(settings, 'EMAIL_TEST_MODE', False)
    email_sent = False
    email_error = None
    
    logger.info(f'📧 Intentando enviar código OTP de recuperación a {usuario.email}')
    logger.info(f'🔑 Código OTP generado: {codigo} (para pruebas/verificación manual)')
    
    if email_test_mode:
        logger.warning(f'⚠️ MODO PRUEBA: No se enviará correo real. Código OTP: {codigo}')
    else:
        try:
            result_queue = queue.Queue()
            
            def send_email_thread():
                try:
                    send_mail(
                        'Código de recuperación de contraseña',
                        f'Tu código de recuperación es: {codigo}. Expira en 10 minutos.',
                        settings.DEFAULT_FROM_EMAIL,
                        [usuario.email],
                        fail_silently=False,
                    )
                    result_queue.put(('success', None))
                except Exception as e:
                    result_queue.put(('error', e))
            
            email_thread = threading.Thread(target=send_email_thread, daemon=True)
            email_thread.start()
            email_thread.join(timeout=10)
            
            if email_thread.is_alive():
                logger.error(f'⏱️ Timeout: El envío de correo tomó más de 10 segundos')
                email_error = 'Timeout: El servidor de correo no respondió a tiempo'
            else:
                result = result_queue.get_nowait()
                if result[0] == 'success':
                    email_sent = True
                    logger.info(f'✅ Correo enviado exitosamente a {usuario.email}')
                else:
                    email_error = str(result[1])
                    logger.error(f'❌ Error al enviar correo: {email_error}')
        except Exception as e:
            email_error = str(e)
            logger.error(f'❌ Error inesperado al enviar correo: {email_error}')

    # Siempre retornar tempToken incluso si falla el email (para permitir pruebas)
    response_data = {
        'ok': True,
        'tempToken': temp_token,
        'email_enviado': email_sent
    }
    
    if email_test_mode:
        response_data['codigo_otp'] = codigo  # Solo en modo prueba
    
    if email_error:
        response_data['error_email'] = email_error
        logger.warning(f'⚠️ Usuario creado pero email falló: {email_error}')
    
    return JsonResponse(response_data)

@csrf_exempt
def verificar_otp_recuperacion(request):
    """
    Verificar código OTP para recuperación de contraseña
    """
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

    session_data = request.session.get(temp_token)
    if not session_data or session_data.get('tipo') != 'recuperacion':
        return JsonResponse({'error': 'Token inválido o expirado'}, status=400)

    # Verificar expiración
    if datetime.datetime.now().timestamp() > session_data['expira']:
        del request.session[temp_token]
        return JsonResponse({'error': 'Token expirado'}, status=400)

    # Verificar intentos
    if session_data.get('intentos', 0) >= 3:
        del request.session[temp_token]
        return JsonResponse({'error': 'Demasiados intentos fallidos'}, status=400)

    # Verificar código
    if session_data.get('codigo') != codigo:
        session_data['intentos'] = session_data.get('intentos', 0) + 1
        request.session[temp_token] = session_data
        return JsonResponse({'error': 'Código incorrecto'}, status=400)

    # Código correcto - actualizar token para permitir cambio de contraseña
    request.session[temp_token] = {
        'email': session_data['email'],
        'tipo': 'recuperacion_verificada',
        'expira': (datetime.datetime.now() + datetime.timedelta(minutes=10)).timestamp()
    }

    return JsonResponse({'ok': True, 'mensaje': 'Código verificado correctamente'})

@csrf_exempt
def reenviar_otp_recuperacion(request):
    """
    Reenviar código OTP para recuperación de contraseña
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Método no permitido'}, status=405)

    try:
        data = json.loads(request.body)
        correo = data.get('correo')
    except (json.JSONDecodeError, KeyError):
        return JsonResponse({'error': 'Datos inválidos'}, status=400)

    if not correo:
        return JsonResponse({'error': 'El correo es requerido'}, status=400)

    # Llamar a recuperar_otp con el mismo email
    return recuperar_otp(request)

@csrf_exempt
def actualizar_contrasena_otp(request):
    """
    Actualizar contraseña después de verificar OTP de recuperación
    """
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
    if not session_data or session_data.get('tipo') != 'recuperacion_verificada':
        return JsonResponse({'error': 'Token inválido o no verificado'}, status=400)

    # Verificar expiración
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