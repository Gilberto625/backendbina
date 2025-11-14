# accounts/email_utils.py
from django.core.mail import send_mail
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def enviar_correo_verificacion(email, codigo):
    """
    Envía un correo de verificación con código 2FA
    """
    asunto = 'Código de verificación - Bina App'
    mensaje = f"""
    ¡Hola!

    Tu código de verificación es: {codigo}

    Este código expira en 5 minutos.

    Si no solicitaste este código, ignora este correo.

    Saludos,
    El equipo de Bina App
    """

    try:
        send_mail(
            asunto,
            mensaje,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
        logger.info(f"Correo de verificación enviado a {email}")
        return True
    except Exception as e:
        logger.error(f"Error al enviar correo de verificación a {email}: {str(e)}")
        return False


def enviar_correo_recuperacion(email, token, dominio='https://frontbina.vercel.app'):
    """
    Envía un correo con enlace de recuperación de contraseña
    """
    enlace = f"{dominio}/reset-password?token={token}"

    asunto = 'Recuperación de contraseña - Bina App'
    mensaje = f"""
    ¡Hola!

    Recibimos una solicitud para restablecer tu contraseña.

    Haz clic en el siguiente enlace para restablecer tu contraseña:
    {enlace}

    Este enlace expira en 30 minutos.

    Si no solicitaste restablecer tu contraseña, ignora este correo.

    Saludos,
    El equipo de Bina App
    """

    try:
        send_mail(
            asunto,
            mensaje,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
        logger.info(f"Correo de recuperación enviado a {email}")
        return True
    except Exception as e:
        logger.error(f"Error al enviar correo de recuperación a {email}: {str(e)}")
        return False


def enviar_correo_bienvenida(email, nombre):
    """
    Envía un correo de bienvenida después de verificar la cuenta
    """
    asunto = '¡Bienvenido a Bina App!'
    mensaje = f"""
    ¡Hola {nombre}!

    Tu cuenta ha sido verificada exitosamente.

    Ya puedes disfrutar de todos los servicios de Bina App.

    Para mayor seguridad, te recomendamos:
    1. Configurar autenticación de dos factores (TOTP)
    2. Generar códigos de respaldo

    Saludos,
    El equipo de Bina App
    """

    try:
        send_mail(
            asunto,
            mensaje,
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )
        logger.info(f"Correo de bienvenida enviado a {email}")
        return True
    except Exception as e:
        logger.error(f"Error al enviar correo de bienvenida a {email}: {str(e)}")
        return False
