# accounts/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.hashers import make_password, check_password

class Usuario(AbstractUser):
    telefono = models.CharField(max_length=15, blank=True)
    pregunta_secreta = models.CharField(max_length=255, blank=True)
    respuesta_secreta = models.CharField(max_length=255, blank=True)  # Ahora se almacena hasheada
    verificado = models.BooleanField(default=False)

    # Campos para OTP con SendGrid
    codigo_otp = models.CharField(max_length=255, null=True, blank=True)  # Aumentado para tokens
    otp_expira = models.DateTimeField(null=True, blank=True)
    confirmado = models.BooleanField(default=False)
    totp_enabled = models.BooleanField(default=False)

    # Campo para backup codes (almacenado como JSON string hasheado)
    backup_codes = models.TextField(blank=True, null=True)

    # Campos para protección contra fuerza bruta
    intentos_fallidos = models.IntegerField(default=0)
    bloqueado_hasta = models.DateTimeField(null=True, blank=True)

    def __str__(self):
        return self.email

    def set_respuesta_secreta(self, respuesta):
        """
        Hashea y almacena la respuesta secreta
        Se normaliza a minúsculas para comparación case-insensitive
        """
        if respuesta:
            self.respuesta_secreta = make_password(respuesta.lower().strip())

    def check_respuesta_secreta(self, respuesta):
        """
        Verifica si la respuesta secreta es correcta
        """
        if not self.respuesta_secreta or not respuesta:
            return False
        return check_password(respuesta.lower().strip(), self.respuesta_secreta)