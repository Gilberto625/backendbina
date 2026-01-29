# notificaciones/models.py
from django.db import models
from django.contrib.auth import get_user_model

Usuario = get_user_model()

# Tipos de notificación
TIPO_NOTIFICACION_CHOICES = [
    ('email', 'Email'),
    ('sms', 'SMS'),
    ('push', 'Push Notification'),
]

# Canales de notificación
CANAL_CHOICES = [
    ('email', 'Email'),
    ('sms', 'SMS'),
    ('push', 'Push Notification'),
]

# Estados de notificación
ESTADO_NOTIFICACION_CHOICES = [
    ('pendiente', 'Pendiente'),
    ('enviada', 'Enviada'),
    ('fallida', 'Fallida'),
    ('cancelada', 'Cancelada'),
]

# Tipos de eventos
TIPO_EVENTO_CHOICES = [
    ('recordatorio_cita', 'Recordatorio de Cita'),
    ('cita_confirmada', 'Cita Confirmada'),
    ('cita_cancelada', 'Cita Cancelada'),
    ('cita_modificada', 'Cita Modificada'),
    ('compra_confirmada', 'Compra Confirmada'),
    ('pago_recibido', 'Pago Recibido'),
    ('producto_disponible', 'Producto Disponible'),
    ('stock_bajo', 'Stock Bajo'),
    ('bienvenida', 'Bienvenida'),
    ('otro', 'Otro'),
]


class Notificacion(models.Model):
    """Registro de notificaciones enviadas"""
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='notificaciones',
        null=True,
        blank=True,
        help_text="Usuario destinatario (null para notificaciones globales)"
    )
    
    canal = models.CharField(max_length=20, choices=CANAL_CHOICES, default='email')
    tipo_evento = models.CharField(max_length=50, choices=TIPO_EVENTO_CHOICES, default='otro')
    
    asunto = models.CharField(max_length=200, blank=True)
    mensaje = models.TextField()
    
    # Relaciones opcionales
    cita = models.ForeignKey(
        'citas.Cita',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notificaciones'
    )
    compra = models.ForeignKey(
        'productos.Compra',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notificaciones'
    )
    pago = models.ForeignKey(
        'pagos.Pago',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='notificaciones'
    )
    
    # Estado y tracking
    estado = models.CharField(
        max_length=20,
        choices=ESTADO_NOTIFICACION_CHOICES,
        default='pendiente'
    )
    fecha_programada = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Fecha programada para envío (null para envío inmediato)"
    )
    fecha_enviada = models.DateTimeField(null=True, blank=True)
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    
    # Información de envío
    destinatario = models.CharField(
        max_length=255,
        help_text="Email, teléfono o token según el canal"
    )
    id_externo = models.CharField(
        max_length=100,
        blank=True,
        help_text="ID de la notificación en el servicio externo (Resend, Twilio, etc.)"
    )
    error = models.TextField(blank=True, help_text="Mensaje de error si falló")
    
    # Metadata
    metadata = models.JSONField(
        default=dict,
        blank=True,
        help_text="Datos adicionales en formato JSON"
    )

    class Meta:
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'
        ordering = ['-fecha_creacion']
        indexes = [
            models.Index(fields=['usuario', 'estado']),
            models.Index(fields=['canal', 'estado']),
            models.Index(fields=['tipo_evento', 'fecha_creacion']),
            models.Index(fields=['fecha_programada', 'estado']),
        ]

    def __str__(self):
        return f"{self.get_canal_display()} - {self.get_tipo_evento_display()} - {self.destinatario}"
    
    def marcar_enviada(self):
        """Marca la notificación como enviada"""
        from django.utils import timezone
        self.estado = 'enviada'
        self.fecha_enviada = timezone.now()
        self.save()
    
    def marcar_fallida(self, error_msg=''):
        """Marca la notificación como fallida"""
        self.estado = 'fallida'
        self.error = error_msg
        self.save()


# Plataformas de dispositivos
PLATAFORMA_CHOICES = [
    ('android', 'Android'),
    ('ios', 'iOS'),
    ('web', 'Web'),
]


class DispositivoFCM(models.Model):
    """
    Almacena los tokens FCM de dispositivos de usuarios para notificaciones push.
    Un usuario puede tener múltiples dispositivos registrados.
    """
    usuario = models.ForeignKey(
        Usuario,
        on_delete=models.CASCADE,
        related_name='dispositivos_fcm',
        help_text="Usuario propietario del dispositivo"
    )
    
    token = models.CharField(
        max_length=255,
        unique=True,
        help_text="Token FCM del dispositivo"
    )
    
    plataforma = models.CharField(
        max_length=20,
        choices=PLATAFORMA_CHOICES,
        default='android',
        help_text="Plataforma del dispositivo"
    )
    
    nombre_dispositivo = models.CharField(
        max_length=100,
        blank=True,
        help_text="Nombre identificador del dispositivo (ej: 'iPhone de Juan')"
    )
    
    activo = models.BooleanField(
        default=True,
        help_text="Si el token es válido y activo"
    )
    
    fecha_registro = models.DateTimeField(auto_now_add=True)
    fecha_ultimo_uso = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = 'Dispositivo FCM'
        verbose_name_plural = 'Dispositivos FCM'
        ordering = ['-fecha_ultimo_uso']
        indexes = [
            models.Index(fields=['usuario', 'activo']),
            models.Index(fields=['token']),
        ]
    
    def __str__(self):
        return f"{self.usuario.email} - {self.get_plataforma_display()} - {self.nombre_dispositivo or 'Sin nombre'}"
