# citas/models.py
from django.db import models
from django.utils import timezone
from accounts.models import Usuario

# Estados de cita
ESTADO_CITA_CHOICES = [
    ('pendiente', 'Pendiente'),
    ('confirmada', 'Confirmada'),
    ('en_proceso', 'En Proceso'),
    ('completada', 'Completada'),
    ('cancelada', 'Cancelada'),
    ('no_asistio', 'No Asistió'),
]

# Métodos de pago
METODO_PAGO_CHOICES = [
    ('efectivo', 'Efectivo'),
    ('tarjeta', 'Tarjeta'),
    ('transferencia', 'Transferencia'),
    ('mercado_pago', 'Mercado Pago'),
]

class Silla(models.Model):
    """Representa una silla física en la barbería"""
    numero = models.IntegerField(unique=True, help_text="Número de la silla (Silla 1, Silla 2, etc.)")
    nombre = models.CharField(max_length=50, help_text="Nombre descriptivo (ej: Silla 1)")
    activa = models.BooleanField(default=True)
    descripcion = models.TextField(blank=True)

    class Meta:
        verbose_name = 'Silla'
        verbose_name_plural = 'Sillas'
        ordering = ['numero']

    def __str__(self):
        return f"Silla {self.numero}"

class Servicio(models.Model):
    """Servicios que ofrece la barbería (corte, barba, combo, etc.)"""
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    precio_base = models.DecimalField(max_digits=10, decimal_places=2)
    duracion_minutos = models.IntegerField(default=30, help_text="Duración estimada en minutos")
    activo = models.BooleanField(default=True)
    categoria = models.CharField(
        max_length=50,
        choices=[
            ('corte', 'Corte de Cabello'),
            ('barba', 'Arreglo de Barba'),
            ('combo', 'Combo (Corte + Barba)'),
            ('tratamiento', 'Tratamiento'),
            ('tinte', 'Tinte'),
        ],
        default='corte'
    )

    class Meta:
        verbose_name = 'Servicio'
        verbose_name_plural = 'Servicios'
        ordering = ['categoria', 'nombre']

    def __str__(self):
        return f"{self.nombre} - ${self.precio_base}"

class Cita(models.Model):
    """Cita agendada en la barbería"""
    cliente = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='citas_cliente')
    barbero = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name='citas_barbero')
    servicio = models.ForeignKey(Servicio, on_delete=models.PROTECT)
    silla = models.ForeignKey(Silla, on_delete=models.PROTECT, null=True, blank=True)
    
    fecha_hora = models.DateTimeField()
    duracion_minutos = models.IntegerField(help_text="Duración real de la cita")
    
    estado = models.CharField(max_length=20, choices=ESTADO_CITA_CHOICES, default='pendiente')
    
    # Información de pago
    precio_total = models.DecimalField(max_digits=10, decimal_places=2)
    anticipo_pagado = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    anticipo_requerido = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    metodo_pago_anticipo = models.CharField(max_length=20, choices=METODO_PAGO_CHOICES, blank=True)
    metodo_pago_restante = models.CharField(max_length=20, choices=METODO_PAGO_CHOICES, blank=True)
    
    # Tracking
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    fecha_asistencia = models.DateTimeField(null=True, blank=True)
    fecha_cancelacion = models.DateTimeField(null=True, blank=True)
    
    # Notas
    notas = models.TextField(blank=True, help_text="Notas adicionales sobre la cita")
    motivo_cancelacion = models.TextField(blank=True)
    
    # Registrado por
    registrado_por = models.ForeignKey(
        Usuario, 
        on_delete=models.SET_NULL, 
        null=True, 
        related_name='citas_registradas',
        help_text="Usuario que registró la cita (secretaria o cliente)"
    )

    class Meta:
        verbose_name = 'Cita'
        verbose_name_plural = 'Citas'
        ordering = ['-fecha_hora']
        indexes = [
            models.Index(fields=['fecha_hora', 'estado']),
            models.Index(fields=['cliente', 'estado']),
            models.Index(fields=['barbero', 'fecha_hora']),
        ]

    def __str__(self):
        return f"Cita {self.id} - {self.cliente.email} - {self.fecha_hora.strftime('%Y-%m-%d %H:%M')}"
    
    def puede_cancelar(self, dias_anticipacion_alta=2, dias_anticipacion_baja=1):
        """Verifica si la cita puede ser cancelada según las reglas de negocio"""
        if self.estado in ['cancelada', 'completada', 'no_asistio']:
            return False
        
        ahora = timezone.now()
        tiempo_restante = self.fecha_hora - ahora
        
        # TODO: Verificar clasificación del día (alta/media/baja demanda)
        # Por ahora, usar regla por defecto
        dias_minimos = dias_anticipacion_baja  # Asumir baja demanda por defecto
        
        return tiempo_restante.days >= dias_minimos
    
    def calcular_fin(self):
        """Calcula la fecha/hora de finalización de la cita"""
        from datetime import timedelta
        return self.fecha_hora + timedelta(minutes=self.duracion_minutos)
    
    def esta_disponible(self):
        """Verifica si la cita está disponible (no cancelada, no completada)"""
        return self.estado in ['pendiente', 'confirmada', 'en_proceso']
    
    def marcar_asistencia(self):
        """Marca la cita como asistida"""
        self.estado = 'completada'
        self.fecha_asistencia = timezone.now()
        self.save()
    
    def marcar_no_asistencia(self):
        """Marca la cita como no asistida"""
        self.estado = 'no_asistio'
        self.fecha_cancelacion = timezone.now()
        self.save()
        
        # Actualizar contador de inasistencias del cliente
        self.cliente.inasistencias_consecutivas += 1
        if self.cliente.inasistencias_consecutivas >= 1:
            # Activar penalización: 10 citas con 50% anticipo
            self.cliente.requiere_anticipo_obligatorio = True
            self.cliente.citas_penalizadas_restantes = 10
        self.cliente.save()
