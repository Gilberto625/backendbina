# notificaciones/services.py
"""
Servicios y lógica de negocio para el módulo de notificaciones
"""
from django.utils import timezone
from django.conf import settings
from django.core.mail import send_mail
from notificaciones.models import Notificacion, DispositivoFCM
from citas.models import Cita
from datetime import timedelta
import logging

logger = logging.getLogger(__name__)

# Firebase Admin SDK para FCM
_firebase_messaging = None

def _get_firebase_messaging():
    """
    Obtiene el módulo de messaging de Firebase Admin SDK.
    Lo inicializa solo una vez (singleton).
    """
    global _firebase_messaging
    
    if _firebase_messaging is not None:
        return _firebase_messaging
    
    # Verificar si FCM está habilitado
    if not getattr(settings, 'FCM_ENABLED', False):
        logger.info("FCM está deshabilitado (FCM_ENABLED=False)")
        return None
    
    try:
        import firebase_admin
        from firebase_admin import messaging, credentials
        
        # Verificar si Firebase ya está inicializado
        try:
            app = firebase_admin.get_app()
            logger.info("Firebase Admin ya estaba inicializado")
        except ValueError:
            # No está inicializado, inicializarlo
            import os
            cred_path = os.path.join(settings.BASE_DIR, 'config', 'firebase-service-account.json')
            
            if not os.path.exists(cred_path):
                logger.error(f"Archivo de credenciales FCM no encontrado: {cred_path}")
                return None
            
            cred = credentials.Certificate(cred_path)
            firebase_admin.initialize_app(cred)
            logger.info("Firebase Admin inicializado correctamente para FCM")
        
        _firebase_messaging = messaging
        return _firebase_messaging
        
    except ImportError:
        logger.error("firebase-admin no está instalado. Ejecuta: pip install firebase-admin")
        return None
    except Exception as e:
        logger.error(f"Error al inicializar Firebase Admin: {str(e)}")
        return None


class NotificacionesService:
    """Servicio para gestión de notificaciones"""
    
    @staticmethod
    def enviar_email(destinatario, asunto, mensaje, usuario=None, metadata=None):
        """
        Envía un email usando Resend (configurado en settings)
        
        Args:
            destinatario: Email del destinatario
            asunto: Asunto del email
            mensaje: Cuerpo del mensaje (HTML o texto)
            usuario: Usuario destinatario (opcional)
            metadata: Dict con metadata adicional
        
        Returns:
            (exito: bool, notificacion: Notificacion, error: str)
        """
        try:
            # Intentar usar Resend si está disponible
            try:
                import resend
                resend.api_key = settings.EMAIL_HOST_PASSWORD
                
                params = {
                    "from": settings.EMAIL_HOST_USER,
                    "to": [destinatario],
                    "subject": asunto,
                    "html": mensaje if '<' in mensaje else f"<p>{mensaje}</p>",
                }
                
                email = resend.Emails.send(params)
                
                # Crear registro de notificación
                notificacion = Notificacion.objects.create(
                    usuario=usuario,
                    canal='email',
                    asunto=asunto,
                    mensaje=mensaje,
                    destinatario=destinatario,
                    estado='enviada',
                    fecha_enviada=timezone.now(),
                    id_externo=email.get('id', ''),
                    metadata=metadata or {}
                )
                
                return True, notificacion, None
                
            except ImportError:
                # Fallback a Django send_mail si Resend no está disponible
                logger.warning("Resend no está instalado, usando Django send_mail")
                
                send_mail(
                    subject=asunto,
                    message=mensaje,
                    from_email=settings.EMAIL_HOST_USER,
                    recipient_list=[destinatario],
                    fail_silently=False,
                )
                
                # Crear registro de notificación
                notificacion = Notificacion.objects.create(
                    usuario=usuario,
                    canal='email',
                    asunto=asunto,
                    mensaje=mensaje,
                    destinatario=destinatario,
                    estado='enviada',
                    fecha_enviada=timezone.now(),
                    metadata=metadata or {}
                )
                
                return True, notificacion, None
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error al enviar email: {error_msg}")
            
            # Crear registro de notificación fallida
            notificacion = Notificacion.objects.create(
                usuario=usuario,
                canal='email',
                asunto=asunto,
                mensaje=mensaje,
                destinatario=destinatario,
                estado='fallida',
                error=error_msg,
                metadata=metadata or {}
            )
            
            return False, notificacion, error_msg
    
    @staticmethod
    def enviar_sms(destinatario, mensaje, usuario=None, metadata=None):
        """
        Envía un SMS
        
        NOTA: Pendiente implementación con Twilio o servicio similar
        
        Args:
            destinatario: Número de teléfono
            mensaje: Mensaje de texto
            usuario: Usuario destinatario (opcional)
            metadata: Dict con metadata adicional
        
        Returns:
            (exito: bool, notificacion: Notificacion, error: str)
        """
        # TODO: Implementar integración con Twilio o servicio SMS
        error_msg = "Integración SMS pendiente (Twilio no configurado)"
        logger.warning(error_msg)
        
        # Crear registro de notificación fallida
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
    
    @staticmethod
    def enviar_push(destinatario, titulo, mensaje, usuario=None, metadata=None, data=None):
        """
        Envía una notificación push usando Firebase Cloud Messaging
        
        Args:
            destinatario: Token FCM del dispositivo
            titulo: Título de la notificación
            mensaje: Mensaje de la notificación
            usuario: Usuario destinatario (opcional)
            metadata: Dict con metadata adicional para guardar en BD
            data: Dict con datos adicionales para la notificación push (payload)
        
        Returns:
            (exito: bool, notificacion: Notificacion, error: str)
        """
        messaging = _get_firebase_messaging()
        
        if messaging is None:
            error_msg = "FCM no está configurado (FCM_ENABLED=False o firebase-admin no disponible)"
            logger.warning(error_msg)
            
            # Crear registro de notificación fallida
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
        
        try:
            # Construir el mensaje FCM
            fcm_message = messaging.Message(
                notification=messaging.Notification(
                    title=titulo,
                    body=mensaje,
                ),
                data=data or {},
                token=destinatario,
                # Configuración Android
                android=messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(
                        icon='ic_notification',
                        color='#D4AF37',  # Dorado de la barbería
                        sound='default',
                    ),
                ),
                # Configuración iOS
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            sound='default',
                            badge=1,
                        ),
                    ),
                ),
            )
            
            # Enviar el mensaje
            response = messaging.send(fcm_message)
            logger.info(f"Notificación push enviada: {response}")
            
            # Crear registro de notificación exitosa
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
            
            # Actualizar fecha de último uso del dispositivo
            DispositivoFCM.objects.filter(token=destinatario).update(fecha_ultimo_uso=timezone.now())
            
            return True, notificacion, None
            
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error al enviar push: {error_msg}")
            
            # Si el token es inválido, marcarlo como inactivo
            if 'registration-token-not-registered' in error_msg.lower() or \
               'invalid-registration-token' in error_msg.lower():
                DispositivoFCM.objects.filter(token=destinatario).update(activo=False)
                logger.info(f"Token FCM marcado como inactivo: {destinatario[:20]}...")
            
            # Crear registro de notificación fallida
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
    
    @staticmethod
    def enviar_push_a_usuario(usuario, titulo, mensaje, metadata=None, data=None):
        """
        Envía notificación push a todos los dispositivos activos de un usuario
        
        Args:
            usuario: Objeto Usuario
            titulo: Título de la notificación
            mensaje: Mensaje de la notificación
            metadata: Dict con metadata adicional
            data: Dict con datos adicionales para la notificación push
        
        Returns:
            (enviadas: int, fallidas: int, notificaciones: list)
        """
        dispositivos = DispositivoFCM.objects.filter(usuario=usuario, activo=True)
        
        enviadas = 0
        fallidas = 0
        notificaciones = []
        
        for dispositivo in dispositivos:
            exito, notificacion, error = NotificacionesService.enviar_push(
                destinatario=dispositivo.token,
                titulo=titulo,
                mensaje=mensaje,
                usuario=usuario,
                metadata=metadata,
                data=data
            )
            notificaciones.append(notificacion)
            if exito:
                enviadas += 1
            else:
                fallidas += 1
        
        return enviadas, fallidas, notificaciones
    
    @staticmethod
    def enviar_push_multiple(tokens, titulo, mensaje, data=None):
        """
        Envía notificación push a múltiples tokens (broadcast)
        
        Args:
            tokens: Lista de tokens FCM
            titulo: Título de la notificación
            mensaje: Mensaje de la notificación
            data: Dict con datos adicionales
        
        Returns:
            (exitosos: int, fallidos: int, response)
        """
        messaging = _get_firebase_messaging()
        
        if messaging is None:
            logger.warning("FCM no está configurado para envío múltiple")
            return 0, len(tokens), None
        
        if not tokens:
            return 0, 0, None
        
        try:
            # Construir el mensaje multicast
            multicast_message = messaging.MulticastMessage(
                notification=messaging.Notification(
                    title=titulo,
                    body=mensaje,
                ),
                data=data or {},
                tokens=tokens,
                android=messaging.AndroidConfig(
                    priority='high',
                    notification=messaging.AndroidNotification(
                        icon='ic_notification',
                        color='#D4AF37',
                        sound='default',
                    ),
                ),
                apns=messaging.APNSConfig(
                    payload=messaging.APNSPayload(
                        aps=messaging.Aps(
                            sound='default',
                            badge=1,
                        ),
                    ),
                ),
            )
            
            # Enviar a múltiples dispositivos
            response = messaging.send_each_for_multicast(multicast_message)
            
            logger.info(f"Push múltiple: {response.success_count} exitosos, {response.failure_count} fallidos")
            
            # Marcar tokens inválidos como inactivos
            if response.failure_count > 0:
                for idx, send_response in enumerate(response.responses):
                    if not send_response.success:
                        error = str(send_response.exception) if send_response.exception else ''
                        if 'registration-token-not-registered' in error.lower() or \
                           'invalid-registration-token' in error.lower():
                            DispositivoFCM.objects.filter(token=tokens[idx]).update(activo=False)
            
            return response.success_count, response.failure_count, response
            
        except Exception as e:
            logger.error(f"Error en push múltiple: {str(e)}")
            return 0, len(tokens), None
    
    @staticmethod
    def programar_recordatorio_cita(cita, horas_antes=24):
        """
        Programa un recordatorio de cita
        
        Args:
            cita: Objeto Cita
            horas_antes: Horas antes de la cita para enviar el recordatorio
        
        Returns:
            Notificacion creada
        """
        fecha_recordatorio = cita.fecha_hora - timedelta(hours=horas_antes)
        
        # Solo programar si la fecha de recordatorio es futura
        if fecha_recordatorio <= timezone.now():
            return None
        
        asunto = f"Recordatorio: Cita el {cita.fecha_hora.strftime('%d/%m/%Y a las %H:%M')}"
        mensaje = f"""
        <h2>Recordatorio de Cita</h2>
        <p>Hola {cita.cliente.get_full_name() or cita.cliente.email},</p>
        <p>Te recordamos que tienes una cita programada:</p>
        <ul>
            <li><strong>Fecha y hora:</strong> {cita.fecha_hora.strftime('%d/%m/%Y a las %H:%M')}</li>
            <li><strong>Servicio:</strong> {cita.servicio.nombre}</li>
            <li><strong>Precio:</strong> ${cita.precio_total}</li>
        </ul>
        <p>¡Te esperamos!</p>
        """
        
        notificacion = Notificacion.objects.create(
            usuario=cita.cliente,
            canal='email',
            tipo_evento='recordatorio_cita',
            asunto=asunto,
            mensaje=mensaje,
            destinatario=cita.cliente.email,
            cita=cita,
            estado='pendiente',
            fecha_programada=fecha_recordatorio,
            metadata={
                'horas_antes': horas_antes,
                'cita_id': cita.id,
            }
        )
        
        return notificacion
    
    @staticmethod
    def enviar_notificacion_cita_confirmada(cita):
        """
        Envía notificación cuando se confirma una cita
        
        Args:
            cita: Objeto Cita
        
        Returns:
            Notificacion enviada
        """
        asunto = f"Cita confirmada - {cita.servicio.nombre}"
        mensaje = f"""
        <h2>Cita Confirmada</h2>
        <p>Hola {cita.cliente.get_full_name() or cita.cliente.email},</p>
        <p>Tu cita ha sido confirmada:</p>
        <ul>
            <li><strong>Fecha y hora:</strong> {cita.fecha_hora.strftime('%d/%m/%Y a las %H:%M')}</li>
            <li><strong>Servicio:</strong> {cita.servicio.nombre}</li>
            <li><strong>Precio:</strong> ${cita.precio_total}</li>
        </ul>
        <p>¡Te esperamos!</p>
        """
        
        exito, notificacion, error = NotificacionesService.enviar_email(
            destinatario=cita.cliente.email,
            asunto=asunto,
            mensaje=mensaje,
            usuario=cita.cliente,
            metadata={'cita_id': cita.id, 'tipo': 'confirmacion'}
        )
        
        if exito:
            notificacion.cita = cita
            notificacion.tipo_evento = 'cita_confirmada'
            notificacion.save()
        
        return notificacion
    
    @staticmethod
    def procesar_notificaciones_programadas():
        """
        Procesa las notificaciones programadas que deben enviarse
        
        NOTA: Debe ejecutarse periódicamente (ej: cada minuto con Celery o cron)
        
        Returns:
            int: Número de notificaciones procesadas
        """
        ahora = timezone.now()
        
        # Buscar notificaciones pendientes programadas para ahora o antes
        notificaciones = Notificacion.objects.filter(
            estado='pendiente',
            fecha_programada__lte=ahora
        )
        
        procesadas = 0
        for notificacion in notificaciones:
            try:
                if notificacion.canal == 'email':
                    exito, _, error = NotificacionesService.enviar_email(
                        destinatario=notificacion.destinatario,
                        asunto=notificacion.asunto,
                        mensaje=notificacion.mensaje,
                        usuario=notificacion.usuario,
                        metadata=notificacion.metadata
                    )
                    if exito:
                        notificacion.marcar_enviada()
                    else:
                        notificacion.marcar_fallida(error)
                elif notificacion.canal == 'sms':
                    exito, _, error = NotificacionesService.enviar_sms(
                        destinatario=notificacion.destinatario,
                        mensaje=notificacion.mensaje,
                        usuario=notificacion.usuario,
                        metadata=notificacion.metadata
                    )
                    if exito:
                        notificacion.marcar_enviada()
                    else:
                        notificacion.marcar_fallida(error)
                elif notificacion.canal == 'push':
                    exito, _, error = NotificacionesService.enviar_push(
                        destinatario=notificacion.destinatario,
                        titulo=notificacion.asunto,
                        mensaje=notificacion.mensaje,
                        usuario=notificacion.usuario,
                        metadata=notificacion.metadata
                    )
                    if exito:
                        notificacion.marcar_enviada()
                    else:
                        notificacion.marcar_fallida(error)
                
                procesadas += 1
            except Exception as e:
                logger.error(f"Error al procesar notificación {notificacion.id}: {str(e)}")
                notificacion.marcar_fallida(str(e))
        
        return procesadas
