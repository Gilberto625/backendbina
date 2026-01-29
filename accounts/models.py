# accounts/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser

# Opciones de roles
ROLES_CHOICES = [
    ('cliente', 'Cliente'),
    ('secretaria', 'Secretaria'),
    ('barbero', 'Barbero'),
    ('administrador', 'Administrador'),
]

class Usuario(AbstractUser):
    telefono = models.CharField(max_length=15, blank=True)
    pregunta_secreta = models.CharField(max_length=255, blank=True)
    respuesta_secreta = models.CharField(max_length=255, blank=True)
    verificado = models.BooleanField(default=False)
    confirmado = models.BooleanField(default=False)
    intentos_fallidos = models.IntegerField(default=0)  # Intentos de login fallidos
    rol = models.CharField(max_length=20, choices=ROLES_CHOICES, default='cliente')
    fecha_registro = models.DateTimeField(auto_now_add=True)
    activo = models.BooleanField(default=True)
    
    # Campos para tracking de penalizaciones (reglas de negocio)
    inasistencias_consecutivas = models.IntegerField(default=0)
    requiere_anticipo_obligatorio = models.BooleanField(default=False)
    citas_penalizadas_restantes = models.IntegerField(default=0)  # 10 citas con 50% anticipo

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'
        ordering = ['-fecha_registro']

    def __str__(self):
        return f"{self.email} ({self.get_rol_display()})"
    
    def es_cliente(self):
        return self.rol == 'cliente'
    
    def es_secretaria(self):
        return self.rol == 'secretaria'
    
    def es_barbero(self):
        return self.rol == 'barbero'
    
    def es_administrador(self):
        return self.rol == 'administrador'
    
    def puede_agendar_sin_anticipo(self):
        """Verifica si el cliente puede agendar sin anticipo (primera cita o sin penalización)"""
        if not self.es_cliente():
            return False
        # Primera cita: no tiene citas previas
        # Usar try/except para evitar importación circular
        try:
            from citas.models import Cita
            tiene_citas_previas = Cita.objects.filter(cliente=self).exists()
            if not tiene_citas_previas:
                return True
        except:
            # Si no existe el modelo aún, asumir que puede agendar
            return True
        # Sin penalización activa
        return not self.requiere_anticipo_obligatorio