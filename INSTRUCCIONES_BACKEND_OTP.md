# 📋 Instrucciones para Implementar OTP con SendGrid en el Backend

## 🎯 Objetivo
Implementar verificación OTP (One-Time Password) con SendGrid en tu backend Django, siguiendo el patrón de Nova_Graf-main.

---

## 📦 PASO 1: Instalar Dependencias

En tu proyecto backend, ejecuta:

```bash
pip install sendgrid python-dotenv
```

O si usas `requirements.txt`:

```txt
sendgrid>=6.9.0
python-dotenv>=1.0.0
```

---

## ⚙️ PASO 2: Configurar Variables de Entorno

### 2.1 Crear/Actualizar archivo `.env`

En la raíz de tu proyecto backend, crea o actualiza el archivo `.env`:

```env
SENDGRID_API_KEY=tu-api-key-de-sendgrid-aqui
SENDGRID_FROM_EMAIL=tu-email@example.com
SENDGRID_FROM_NAME=modulo usuario
```

### 2.2 Configurar en `settings.py`

Agrega estas líneas a tu archivo `settings.py`:

```python
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

# Configuración de SendGrid
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY', '')
SENDGRID_FROM_EMAIL = os.getenv('SENDGRID_FROM_EMAIL', '')
SENDGRID_FROM_NAME = os.getenv('SENDGRID_FROM_NAME', 'modulo usuario')
```

---

## 🗄️ PASO 3: Actualizar Modelo de Usuario

Asegúrate de que tu modelo `Usuario` tenga estos campos. Si no los tienes, agrega una migración:

```python
# models.py
from django.db import models
from django.utils import timezone

class Usuario(models.Model):
    # ... tus campos existentes ...
    nombre = models.CharField(max_length=100)
    apellidopaterno = models.CharField(max_length=100)
    apellidomaterno = models.CharField(max_length=100, blank=True)
    username = models.CharField(max_length=50, unique=True)
    correo = models.EmailField(unique=True)
    contrasena = models.CharField(max_length=255)  # Hasheada
    telefono = models.CharField(max_length=20, blank=True)
    preguntasecreta = models.CharField(max_length=255)
    respuestasecreta = models.CharField(max_length=255)
    
    # ✅ CAMPOS NUEVOS PARA OTP
    codigo_otp = models.CharField(max_length=6, null=True, blank=True)
    otp_expira = models.DateTimeField(null=True, blank=True)
    confirmado = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.correo
```

### 3.1 Crear Migración

```bash
python manage.py makemigrations
python manage.py migrate
```

---

## 🔧 PASO 4: Crear Servicio de SendGrid

Crea un nuevo archivo `utils/sendgrid_otp_service.py` (o en la carpeta que uses para utilidades):

```python
# utils/sendgrid_otp_service.py
import random
from datetime import timedelta
from django.utils import timezone
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from django.conf import settings


def generar_codigo_otp() -> str:
    """Genera un código OTP de 6 dígitos"""
    return str(random.randint(100000, 999999))


def enviar_otp_email(correo: str, codigo_otp: str) -> bool:
    """
    Envía un código OTP por email usando SendGrid
    
    Args:
        correo: Email del destinatario
        codigo_otp: Código OTP de 6 dígitos
        
    Returns:
        bool: True si se envió correctamente, False en caso contrario
    """
    try:
        message = Mail(
            from_email=(settings.SENDGRID_FROM_EMAIL, settings.SENDGRID_FROM_NAME),
            to_emails=correo,
            subject='Código de verificación - Módulo Usuario',
            html_content=f'''
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #1976d2;">Bienvenido</h2>
                    <p>Tu código de verificación es:</p>
                    <h3 style="font-size: 32px; color: #1976d2; letter-spacing: 8px; text-align: center; 
                               background-color: #f5f5f5; padding: 20px; border-radius: 8px;">
                        {codigo_otp}
                    </h3>
                    <p>Este código expira en 10 minutos.</p>
                    <p style="color: #666; font-size: 12px;">
                        Si no solicitaste este código, ignora este mensaje.
                    </p>
                </div>
            '''
        )
        
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)
        
        if response.status_code == 202:
            print(f"✅ Correo OTP enviado a: {correo}")
            return True
        else:
            print(f"❌ Error enviando correo: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error enviando correo OTP: {str(e)}")
        return False


def enviar_otp_recuperacion(correo: str, codigo_otp: str) -> bool:
    """
    Envía un código OTP para recuperación de contraseña
    
    Args:
        correo: Email del destinatario
        codigo_otp: Código OTP de 6 dígitos
        
    Returns:
        bool: True si se envió correctamente, False en caso contrario
    """
    try:
        message = Mail(
            from_email=(settings.SENDGRID_FROM_EMAIL, settings.SENDGRID_FROM_NAME),
            to_emails=correo,
            subject='Recuperación de contraseña - Módulo Usuario',
            html_content=f'''
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #d32f2f;">Recuperación de contraseña</h2>
                    <p>Hemos recibido una solicitud para restablecer tu contraseña.</p>
                    <p>Tu código de verificación es:</p>
                    <h3 style="font-size: 32px; color: #d32f2f; letter-spacing: 8px; text-align: center; 
                               background-color: #ffebee; padding: 20px; border-radius: 8px;">
                        {codigo_otp}
                    </h3>
                    <p>Este código expira en 10 minutos.</p>
                    <p style="color: #666; font-size: 12px;">
                        Si no solicitaste este cambio, ignora este mensaje.
                    </p>
                </div>
            '''
        )
        
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)
        
        if response.status_code == 202:
            print(f"✅ Correo de recuperación enviado a: {correo}")
            return True
        else:
            print(f"❌ Error enviando correo: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ Error enviando correo de recuperación: {str(e)}")
        return False
```

---

## 🛣️ PASO 5: Crear/Actualizar Vistas

Crea o actualiza tus vistas en `views.py` (o en el archivo donde tengas tus vistas de autenticación):

```python
# views.py
import json
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.hashers import make_password, check_password
from .models import Usuario
from .utils.sendgrid_otp_service import generar_codigo_otp, enviar_otp_email, enviar_otp_recuperacion


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
        except Usuario.DoesNotExist:
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
            usuario = Usuario.objects.get(correo=correo)
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
            usuario = Usuario.objects.get(correo=correo)
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
        except Usuario.DoesNotExist:
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
            usuario = Usuario.objects.get(correo=correo)
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
        except Usuario.DoesNotExist:
            return JsonResponse({
                'error': 'Usuario no encontrado'
            }, status=404)
        
        # Verificar que el código OTP aún sea válido
        if not usuario.codigo_otp or not usuario.otp_expira or usuario.otp_expira < timezone.now():
            return JsonResponse({
                'error': 'Sesión expirada. Solicita un nuevo código.'
            }, status=400)
        
        # Actualizar contraseña (hasheada)
        usuario.contrasena = make_password(nueva_contrasena)
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
```

---

## 🔄 PASO 6: Actualizar Vista de Registro

Modifica tu vista de registro existente para que envíe OTP:

```python
@csrf_exempt
@require_http_methods(["POST"])
def register(request):
    """
    Registra un usuario y envía código OTP por email
    """
    try:
        data = json.loads(request.body)
        
        # Validaciones
        correo = data.get('correo')
        if Usuario.objects.filter(correo=correo).exists():
            return JsonResponse({
                'error': 'Este correo ya está registrado'
            }, status=400)
        
        # Generar código OTP
        codigo_otp = generar_codigo_otp()
        otp_expira = timezone.now() + timedelta(minutes=10)
        
        # Crear usuario
        usuario = Usuario.objects.create(
            nombre=data.get('nombre'),
            apellidopaterno=data.get('apellidopaterno'),
            apellidomaterno=data.get('apellidomaterno', ''),
            username=data.get('username'),
            correo=correo,
            contrasena=make_password(data.get('contrasena')),  # Hashear
            telefono=data.get('telefono', ''),
            preguntasecreta=data.get('preguntasecreta'),
            respuestasecreta=data.get('respuestasecreta'),
            codigo_otp=codigo_otp,
            otp_expira=otp_expira,
            confirmado=False
        )
        
        # Enviar código OTP por email
        if enviar_otp_email(correo, codigo_otp):
            return JsonResponse({
                'message': 'Usuario registrado. Ingresa el código OTP enviado a tu correo.',
                'tempToken': str(usuario.id),  # O genera un token temporal más seguro
                'destino': 'email'
            }, status=201)
        else:
            return JsonResponse({
                'error': 'Usuario registrado, pero no se pudo enviar el correo de activación'
            }, status=500)
            
    except Exception as e:
        return JsonResponse({
            'error': f'Error al registrar usuario: {str(e)}'
        }, status=500)
```

---

## 🛣️ PASO 7: Agregar URLs

En tu archivo `urls.py`, agrega estas rutas:

```python
# urls.py
from django.urls import path
from . import views

urlpatterns = [
    # ... tus rutas existentes ...
    
    # Rutas OTP
    path('api/usuarios/verificar-otp/', views.verificar_otp_registro, name='verificar_otp'),
    path('api/usuarios/reenviar-otp/', views.reenviar_otp, name='reenviar_otp'),
    path('api/usuarios/recuperar-otp/', views.solicitar_recuperacion_otp, name='recuperar_otp'),
    path('api/usuarios/verificar-otp-recuperacion/', views.verificar_otp_recuperacion, name='verificar_otp_recuperacion'),
    path('api/usuarios/reenviar-otp-recuperacion/', views.reenviar_otp_recuperacion, name='reenviar_otp_recuperacion'),
    path('api/usuarios/actualizar-contrasena-otp/', views.actualizar_contrasena_otp, name='actualizar_contrasena_otp'),
]
```

---

## ✅ PASO 8: Verificar Implementación

### 8.1 Probar Registro con OTP

1. Registra un usuario → Deberías recibir un email con código OTP
2. Verifica el código → La cuenta debería activarse
3. Intenta iniciar sesión → Debería funcionar

### 8.2 Probar Recuperación con OTP

1. Solicita recuperación → Deberías recibir un email con código OTP
2. Verifica el código → Debería validarse
3. Cambia la contraseña → Debería actualizarse

---

## 🔒 PASO 9: Mejoras de Seguridad (Opcional)

### 9.1 Rate Limiting

Instala `django-ratelimit`:

```bash
pip install django-ratelimit
```

Agrega a tus vistas:

```python
from django_ratelimit.decorators import ratelimit

@ratelimit(key='ip', rate='5/m', method='POST')
@csrf_exempt
@require_http_methods(["POST"])
def verificar_otp_registro(request):
    # ... tu código ...
```

### 9.2 Tokens Temporales Más Seguros

En lugar de usar el ID del usuario como `tempToken`, genera tokens únicos:

```python
import secrets

def generar_token_temporal():
    return secrets.token_urlsafe(32)
```

---

## 📝 Checklist de Implementación

- [ ] Instalar dependencias (`sendgrid`, `python-dotenv`)
- [ ] Configurar variables de entorno en `.env` y `settings.py`
- [ ] Agregar campos OTP al modelo `Usuario`
- [ ] Crear migración y ejecutarla
- [ ] Crear servicio `sendgrid_otp_service.py`
- [ ] Implementar vistas OTP
- [ ] Actualizar vista de registro
- [ ] Agregar URLs
- [ ] Probar flujo completo
- [ ] Implementar mejoras de seguridad (opcional)

---

## 🆘 Solución de Problemas

### Error: "ModuleNotFoundError: No module named 'sendgrid'"
**Solución:** Ejecuta `pip install sendgrid`

### Error: "No se pudo enviar el correo"
**Solución:** 
- Verifica que `SENDGRID_API_KEY` esté correctamente configurado
- Verifica que el email remitente esté verificado en SendGrid
- Revisa los logs del servidor para más detalles

### Error: "Código expirado"
**Solución:** Los códigos expiran en 10 minutos. Usa el botón "Reenviar código"

### Error: "Usuario no encontrado"
**Solución:** Verifica que el `tempToken` sea correcto y que el usuario exista en la base de datos

---

## 📚 Archivos de Referencia

En este proyecto encontrarás:
- `backend_reference/sendgrid_otp_service.py` - Servicio completo
- `backend_reference/views_otp_example.py` - Vistas de ejemplo
- `backend_reference/README_SENDGRID_OTP.md` - Documentación detallada

---

## ✅ ¡Listo!

Una vez completados estos pasos, tu backend estará listo para usar OTP con SendGrid. El frontend Angular ya está configurado y esperando estos endpoints.

