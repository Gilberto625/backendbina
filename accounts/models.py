# accounts/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
import pyotp
import secrets

class Usuario(AbstractUser):
    telefono = models.CharField(max_length=15, blank=True)
    pregunta_secreta = models.CharField(max_length=255, blank=True)
    respuesta_secreta = models.CharField(max_length=255, blank=True)
    verificado = models.BooleanField(default=False)

    # Campos para TOTP (Google Authenticator)
    totp_secret = models.CharField(max_length=32, blank=True, null=True)
    totp_enabled = models.BooleanField(default=False)

    # Códigos de respaldo (backup codes) - JSON string
    backup_codes = models.TextField(blank=True, null=True)  # Almacena códigos hasheados

    # Token de recuperación de contraseña
    password_reset_token = models.CharField(max_length=100, blank=True, null=True)
    password_reset_expires = models.DateTimeField(blank=True, null=True)

    def __str__(self):
        return self.email

    def generate_totp_secret(self):
        """Genera una nueva clave secreta para TOTP"""
        if not self.totp_secret:
            self.totp_secret = pyotp.random_base32()
            self.save()
        return self.totp_secret

    def get_totp_uri(self):
        """Genera la URI para el QR code de TOTP"""
        if not self.totp_secret:
            self.generate_totp_secret()
        return pyotp.totp.TOTP(self.totp_secret).provisioning_uri(
            name=self.email,
            issuer_name="Bina App"
        )

    def verify_totp(self, token):
        """Verifica un código TOTP"""
        if not self.totp_secret:
            return False
        totp = pyotp.TOTP(self.totp_secret)
        return totp.verify(token, valid_window=1)  # Acepta 1 ventana antes/después

    def generate_backup_codes(self, count=10):
        """Genera códigos de respaldo y los retorna en texto plano"""
        from django.contrib.auth.hashers import make_password
        codes = [secrets.token_hex(4).upper() for _ in range(count)]  # Códigos de 8 caracteres
        # Guardar los códigos hasheados
        hashed_codes = [make_password(code) for code in codes]
        self.backup_codes = '|'.join(hashed_codes)
        self.save()
        return codes  # Retornar códigos en texto plano para mostrar al usuario

    def verify_backup_code(self, code):
        """Verifica y consume un código de respaldo"""
        from django.contrib.auth.hashers import check_password
        if not self.backup_codes:
            return False

        codes = self.backup_codes.split('|')
        for i, hashed_code in enumerate(codes):
            if check_password(code.upper(), hashed_code):
                # Remover el código usado
                codes.pop(i)
                self.backup_codes = '|'.join(codes)
                self.save()
                return True
        return False