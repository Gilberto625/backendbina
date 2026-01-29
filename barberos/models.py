# barberos/models.py
from django.db import models
from accounts.models import Usuario
from citas.models import Servicio

class Barbero(models.Model):
    """Perfil extendido de un barbero con sus servicios y tiempos"""
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='perfil_barbero')
    activo = models.BooleanField(default=True)
    fecha_contratacion = models.DateField(null=True, blank=True)
    especialidades = models.TextField(blank=True, help_text="Especialidades del barbero")
    
    class Meta:
        verbose_name = 'Barbero'
        verbose_name_plural = 'Barberos'
        ordering = ['usuario__first_name', 'usuario__last_name']

    def __str__(self):
        return f"{self.usuario.get_full_name() or self.usuario.email}"

class ServicioBarbero(models.Model):
    """Tiempos estimados de duración de servicios por barbero"""
    barbero = models.ForeignKey(Barbero, on_delete=models.CASCADE, related_name='servicios')
    servicio = models.ForeignKey(Servicio, on_delete=models.CASCADE)
    duracion_minutos = models.IntegerField(help_text="Tiempo estimado que tarda este barbero en realizar el servicio")
    activo = models.BooleanField(default=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Servicio de Barbero'
        verbose_name_plural = 'Servicios de Barberos'
        unique_together = ['barbero', 'servicio']
        ordering = ['barbero', 'servicio']

    def __str__(self):
        return f"{self.barbero.usuario.email} - {self.servicio.nombre} ({self.duracion_minutos} min)"
