# configuracion/models.py
from django.db import models

# Clasificación de demanda
DEMANDA_CHOICES = [
    ('alta', 'Alta Demanda'),
    ('media', 'Media Demanda'),
    ('baja', 'Baja Demanda'),
]

class ConfiguracionSistema(models.Model):
    """Configuración de reglas de negocio del sistema"""
    # Clasificación de días por demanda
    dia_semana = models.IntegerField(
        choices=[
            (0, 'Lunes'),
            (1, 'Martes'),
            (2, 'Miércoles'),
            (3, 'Jueves'),
            (4, 'Viernes'),
            (5, 'Sábado'),
            (6, 'Domingo'),
        ],
        unique=True
    )
    demanda = models.CharField(max_length=10, choices=DEMANDA_CHOICES, default='media')
    
    # Reglas de anticipación según demanda
    dias_anticipacion_alta = models.IntegerField(default=3, help_text="Días de anticipación para agendar en alta demanda")
    dias_anticipacion_media = models.IntegerField(default=2, help_text="Días de anticipación para agendar en media demanda")
    dias_anticipacion_baja = models.IntegerField(default=1, help_text="Días de anticipación para agendar en baja demanda")
    
    # Reglas de cancelación
    dias_cancelacion_alta = models.IntegerField(default=2, help_text="Días de anticipación para cancelar en alta demanda")
    dias_cancelacion_media = models.IntegerField(default=1, help_text="Días de anticipación para cancelar en media demanda")
    dias_cancelacion_baja = models.IntegerField(default=1, help_text="Días de anticipación para cancelar en baja demanda")
    
    # Tiempo de espera máximo (minutos)
    tiempo_espera_maximo = models.IntegerField(default=10, help_text="Minutos máximos de espera antes de cancelar automáticamente")
    
    # Costos de envío
    costo_moto_mandado = models.DecimalField(max_digits=10, decimal_places=2, default=40.00)
    costo_paqueteria = models.DecimalField(max_digits=10, decimal_places=2, default=150.00)
    
    # Penalizaciones
    porcentaje_anticipo_penalizado = models.DecimalField(max_digits=5, decimal_places=2, default=50.00, help_text="Porcentaje de anticipo cuando hay penalización")
    citas_penalizadas = models.IntegerField(default=10, help_text="Número de citas con anticipo obligatorio después de inasistencia")
    
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Configuración del Sistema'
        verbose_name_plural = 'Configuraciones del Sistema'
        ordering = ['dia_semana']

    def __str__(self):
        return f"{self.get_dia_semana_display()} - {self.get_demanda_display()}"
    
    @classmethod
    def get_configuracion_dia(cls, dia_semana):
        """Obtiene la configuración para un día de la semana"""
        try:
            return cls.objects.get(dia_semana=dia_semana)
        except cls.DoesNotExist:
            # Retornar configuración por defecto
            return cls(
                dia_semana=dia_semana,
                demanda='media',
                dias_anticipacion_alta=3,
                dias_anticipacion_media=2,
                dias_anticipacion_baja=1,
                dias_cancelacion_alta=2,
                dias_cancelacion_media=1,
                dias_cancelacion_baja=1,
            )
