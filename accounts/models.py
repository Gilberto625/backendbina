# accounts/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser

class Usuario(AbstractUser):
    telefono = models.CharField(max_length=15, blank=True)
    pregunta_secreta = models.CharField(max_length=255, blank=True)
    respuesta_secreta = models.CharField(max_length=255, blank=True)
    verificado = models.BooleanField(default=False)
    
    # Campos para OTP con SendGrid
    codigo_otp = models.CharField(max_length=6, null=True, blank=True)
    otp_expira = models.DateTimeField(null=True, blank=True)
    confirmado = models.BooleanField(default=False)
    totp_enabled = models.BooleanField(default=False)  # Campo existente en BD
    
    # Campo para backup codes (almacenado como JSON string)
    backup_codes = models.TextField(blank=True, null=True)  # JSON array de códigos

    def __str__(self):
        return self.email