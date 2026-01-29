# Integraciones de Notificaciones Pendientes

## 📋 Estado General

El sistema de notificaciones está funcional con **email completamente implementado**. Las siguientes integraciones están pendientes:

1. **SMS (Twilio)** - Pendiente
2. **Push Notifications (Firebase Cloud Messaging)** - Pendiente

## 📱 1. Integración SMS con Twilio

### Estado Actual
- ✅ Estructura base implementada
- ✅ Modelo de notificación con soporte para SMS
- ✅ Endpoint para enviar SMS (retorna error informativo)
- ⏳ Integración con Twilio pendiente

### Pasos para Implementar

#### 1. Crear cuenta en Twilio
- Ir a https://www.twilio.com/
- Crear cuenta y verificar número de teléfono
- Obtener Account SID y Auth Token desde el dashboard

#### 2. Instalar SDK
```bash
pip install twilio
```

#### 3. Configurar Variables de Entorno
Agregar a `.env` o variables de entorno:
```bash
TWILIO_ACCOUNT_SID=tu_account_sid_aqui
TWILIO_AUTH_TOKEN=tu_auth_token_aqui
TWILIO_PHONE_NUMBER=+1234567890  # Número de Twilio
```

#### 4. Agregar a settings.py
```python
# Twilio Configuration
TWILIO_ACCOUNT_SID = config('TWILIO_ACCOUNT_SID', default='')
TWILIO_AUTH_TOKEN = config('TWILIO_AUTH_TOKEN', default='')
TWILIO_PHONE_NUMBER = config('TWILIO_PHONE_NUMBER', default='')
```

#### 5. Implementar función en `notificaciones/services.py`

Reemplazar la función `enviar_sms()` con:

```python
@staticmethod
def enviar_sms(destinatario, mensaje, usuario=None, metadata=None):
    """
    Envía un SMS usando Twilio
    """
    try:
        from twilio.rest import Client
        
        account_sid = getattr(settings, 'TWILIO_ACCOUNT_SID', None)
        auth_token = getattr(settings, 'TWILIO_AUTH_TOKEN', None)
        from_number = getattr(settings, 'TWILIO_PHONE_NUMBER', None)
        
        if not all([account_sid, auth_token, from_number]):
            error_msg = "Twilio no configurado correctamente"
            logger.warning(error_msg)
            
            notificacion = Notificacion.objects.create(
                usuario=usuario,
                canal='sms',
                mensaje=mensaje,
                destinatario=destinatario,
                estado='fallida',
                error=error_msg,
                metadata=metadata or {}
            )
            return False, notificacion, error_msg
        
        client = Client(account_sid, auth_token)
        
        message = client.messages.create(
            body=mensaje,
            from_=from_number,
            to=destinatario
        )
        
        # Crear registro de notificación
        notificacion = Notificacion.objects.create(
            usuario=usuario,
            canal='sms',
            mensaje=mensaje,
            destinatario=destinatario,
            estado='enviada',
            fecha_enviada=timezone.now(),
            id_externo=message.sid,
            metadata=metadata or {}
        )
        
        return True, notificacion, None
        
    except ImportError:
        error_msg = "Twilio SDK no instalado. Ejecutar: pip install twilio"
        logger.warning(error_msg)
        
        notificacion = Notificacion.objects.create(
            usuario=usuario,
            canal='sms',
            mensaje=mensaje,
            destinatario=destinatario,
            estado='fallida',
            error=error_msg,
            metadata=metadata or {}
        )
        return False, notificacion, error_msg
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error al enviar SMS: {error_msg}")
        
        notificacion = Notificacion.objects.create(
            usuario=usuario,
            canal='sms',
            mensaje=mensaje,
            destinatario=destinatario,
            estado='fallida',
            error=error_msg,
            metadata=metadata or {}
        )
        return False, notificacion, error_msg
```

### Costos
- Twilio ofrece cuenta de prueba gratuita con créditos limitados
- Costos por SMS varían según país (consultar en Twilio)
- Considerar límites de rate limiting

---

## 🔔 2. Integración Push con Firebase Cloud Messaging

### Estado Actual
- ✅ Estructura base implementada
- ✅ Modelo de notificación con soporte para push
- ✅ Endpoint para enviar push (retorna error informativo)
- ⏳ Integración con Firebase Cloud Messaging pendiente
- ⏳ Modelo para tokens FCM pendiente

### Pasos para Implementar

#### 1. Crear Proyecto en Firebase
- Ir a https://console.firebase.google.com/
- Crear nuevo proyecto o usar existente
- Habilitar Cloud Messaging

#### 2. Obtener Credenciales
- Descargar archivo JSON de credenciales de servicio
- Guardar en `config/firebase-service-account.json` (o ruta segura)

#### 3. Instalar SDK
```bash
pip install firebase-admin
```

#### 4. Configurar Variables de Entorno
```bash
FIREBASE_CREDENTIALS_PATH=/path/to/firebase-service-account.json
```

#### 5. Agregar a settings.py
```python
# Firebase Cloud Messaging
FIREBASE_CREDENTIALS_PATH = config('FIREBASE_CREDENTIALS_PATH', default='')
```

#### 6. Crear Modelo para Tokens FCM

Crear en `notificaciones/models.py`:

```python
class TokenFCM(models.Model):
    """Tokens de Firebase Cloud Messaging por dispositivo"""
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='tokens_fcm'
    )
    token = models.CharField(max_length=255, unique=True)
    dispositivo = models.CharField(max_length=100, blank=True)
    plataforma = models.CharField(
        max_length=20,
        choices=[('android', 'Android'), ('ios', 'iOS'), ('web', 'Web')],
        default='web'
    )
    activo = models.BooleanField(default=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Token FCM'
        verbose_name_plural = 'Tokens FCM'
        indexes = [
            models.Index(fields=['usuario', 'activo']),
        ]
    
    def __str__(self):
        return f"{self.usuario.email} - {self.plataforma}"
```

#### 7. Implementar función en `notificaciones/services.py`

Reemplazar la función `enviar_push()` con:

```python
@staticmethod
def enviar_push(destinatario, titulo, mensaje, usuario=None, metadata=None):
    """
    Envía una notificación push usando Firebase Cloud Messaging
    """
    try:
        import firebase_admin
        from firebase_admin import credentials, messaging
        
        # Inicializar Firebase si no está inicializado
        if not firebase_admin._apps:
            cred_path = getattr(settings, 'FIREBASE_CREDENTIALS_PATH', None)
            if not cred_path:
                error_msg = "FIREBASE_CREDENTIALS_PATH no configurado"
                logger.warning(error_msg)
                
                notificacion = Notificacion.objects.create(
                    usuario=usuario,
                    canal='push',
                    asunto=titulo,
                    mensaje=mensaje,
                    destinatario=destinatario,
                    estado='fallida',
                    error=error_msg,
                    metadata=metadata or {}
                )
                return False, notificacion, error_msg
            
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
        
        # Crear mensaje
        message = messaging.Message(
            notification=messaging.Notification(
                title=titulo,
                body=mensaje
            ),
            token=destinatario,
            data=metadata or {}
        )
        
        # Enviar
        response = messaging.send(message)
        
        # Crear registro de notificación
        notificacion = Notificacion.objects.create(
            usuario=usuario,
            canal='push',
            asunto=titulo,
            mensaje=mensaje,
            destinatario=destinatario,
            estado='enviada',
            fecha_enviada=timezone.now(),
            id_externo=response,
            metadata=metadata or {}
        )
        
        return True, notificacion, None
        
    except ImportError:
        error_msg = "Firebase Admin SDK no instalado. Ejecutar: pip install firebase-admin"
        logger.warning(error_msg)
        
        notificacion = Notificacion.objects.create(
            usuario=usuario,
            canal='push',
            asunto=titulo,
            mensaje=mensaje,
            destinatario=destinatario,
            estado='fallida',
            error=error_msg,
            metadata=metadata or {}
        )
        return False, notificacion, error_msg
        
    except Exception as e:
        error_msg = str(e)
        logger.error(f"Error al enviar push: {error_msg}")
        
        notificacion = Notificacion.objects.create(
            usuario=usuario,
            canal='push',
            asunto=titulo,
            mensaje=mensaje,
            destinatario=destinatario,
            estado='fallida',
            error=error_msg,
            metadata=metadata or {}
        )
        return False, notificacion, error_msg
```

#### 8. Crear Endpoints para Tokens FCM

Agregar a `notificaciones/views.py`:

```python
@csrf_exempt
@requiere_autenticacion
def registrar_token_fcm(request):
    """Registra o actualiza un token FCM"""
    # Implementar registro de token
    pass

@csrf_exempt
@requiere_autenticacion
def eliminar_token_fcm(request, token_id):
    """Elimina un token FCM"""
    # Implementar eliminación de token
    pass
```

### Costos
- Firebase Cloud Messaging es gratuito
- Límites generosos para uso normal
- Consultar límites en documentación de Firebase

---

## 📝 Notas Importantes

1. **Seguridad**: Nunca commitear credenciales en el repositorio
2. **Rate Limiting**: Considerar límites de ambos servicios
3. **Testing**: Usar ambientes de prueba antes de producción
4. **Manejo de Errores**: Ambos servicios pueden fallar, manejar apropiadamente
5. **Costos**: Monitorear uso y costos de Twilio

---

*Documento creado - 28 de enero de 2026*
*Actualizar cuando se implementen las integraciones*
