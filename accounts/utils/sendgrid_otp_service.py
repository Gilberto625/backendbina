# accounts/utils/sendgrid_otp_service.py
import random
from datetime import timedelta
from django.utils import timezone
from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail
from django.conf import settings


def generar_codigo_otp() -> str:
    """Genera un código OTP de 6 dígitos"""
    return str(random.randint(100000, 999999))


def enviar_otp_email(correo: str, codigo_otp: str) -> bool:
    """
    Envía un código OTP por email usando SendGrid
    
    Args:
        correo: Email del destinatario
        codigo_otp: Código OTP de 6 dígitos
        
    Returns:
        bool: True si se envió correctamente, False en caso contrario
    """
    # Verificar que SendGrid esté configurado
    if not settings.SENDGRID_API_KEY or settings.SENDGRID_API_KEY == '':
        print("⚠️ SENDGRID_API_KEY no configurada. No se puede enviar email.")
        return False
    
    if not settings.SENDGRID_FROM_EMAIL or settings.SENDGRID_FROM_EMAIL == '':
        print("⚠️ SENDGRID_FROM_EMAIL no configurada. No se puede enviar email.")
        return False
    
    try:
        message = Mail(
            from_email=(settings.SENDGRID_FROM_EMAIL, settings.SENDGRID_FROM_NAME),
            to_emails=correo,
            subject='Código de verificación - Módulo Usuario',
            html_content=f'''
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #1976d2;">Bienvenido</h2>
                    <p>Tu código de verificación es:</p>
                    <h3 style="font-size: 32px; color: #1976d2; letter-spacing: 8px; text-align: center; 
                               background-color: #f5f5f5; padding: 20px; border-radius: 8px;">
                        {codigo_otp}
                    </h3>
                    <p>Este código expira en 10 minutos.</p>
                    <p style="color: #666; font-size: 12px;">
                        Si no solicitaste este código, ignora este mensaje.
                    </p>
                </div>
            '''
        )
        
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)
        
        if response.status_code == 202:
            print(f"✅ Correo OTP enviado a: {correo}")
            return True
        else:
            print(f"❌ Error enviando correo: {response.status_code}")
            return False
            
    except Exception as e:
        import traceback
        print(f"❌ Error enviando correo OTP: {str(e)}")
        print(traceback.format_exc())
        return False


def enviar_otp_recuperacion(correo: str, codigo_otp: str) -> bool:
    """
    Envía un código OTP para recuperación de contraseña
    
    Args:
        correo: Email del destinatario
        codigo_otp: Código OTP de 6 dígitos
        
    Returns:
        bool: True si se envió correctamente, False en caso contrario
    """
    # Verificar que SendGrid esté configurado
    if not settings.SENDGRID_API_KEY or settings.SENDGRID_API_KEY == '':
        print("⚠️ SENDGRID_API_KEY no configurada. No se puede enviar email.")
        return False
    
    if not settings.SENDGRID_FROM_EMAIL or settings.SENDGRID_FROM_EMAIL == '':
        print("⚠️ SENDGRID_FROM_EMAIL no configurada. No se puede enviar email.")
        return False
    
    try:
        message = Mail(
            from_email=(settings.SENDGRID_FROM_EMAIL, settings.SENDGRID_FROM_NAME),
            to_emails=correo,
            subject='Recuperación de contraseña - Módulo Usuario',
            html_content=f'''
                <div style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <h2 style="color: #d32f2f;">Recuperación de contraseña</h2>
                    <p>Hemos recibido una solicitud para restablecer tu contraseña.</p>
                    <p>Tu código de verificación es:</p>
                    <h3 style="font-size: 32px; color: #d32f2f; letter-spacing: 8px; text-align: center; 
                               background-color: #ffebee; padding: 20px; border-radius: 8px;">
                        {codigo_otp}
                    </h3>
                    <p>Este código expira en 10 minutos.</p>
                    <p style="color: #666; font-size: 12px;">
                        Si no solicitaste este cambio, ignora este mensaje.
                    </p>
                </div>
            '''
        )
        
        sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
        response = sg.send(message)
        
        if response.status_code == 202:
            print(f"✅ Correo de recuperación enviado a: {correo}")
            return True
        else:
            print(f"❌ Error enviando correo: {response.status_code}")
            return False
            
    except Exception as e:
        import traceback
        print(f"❌ Error enviando correo de recuperación: {str(e)}")
        print(traceback.format_exc())
        return False

