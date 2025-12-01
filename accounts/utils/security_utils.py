# accounts/utils/security_utils.py
"""
Utilidades de seguridad para autenticación
- Bloqueo por intentos fallidos
- Validación de preguntas secretas
- Revocación de sesiones
"""
from django.utils import timezone
from datetime import timedelta
import re


def verificar_bloqueo(usuario):
    """
    Verifica si un usuario está bloqueado por intentos fallidos
    
    Args:
        usuario: Instancia del modelo Usuario
        
    Returns:
        tuple: (esta_bloqueado, tiempo_restante_segundos, mensaje)
    """
    if usuario.bloqueado_hasta and usuario.bloqueado_hasta > timezone.now():
        tiempo_restante = (usuario.bloqueado_hasta - timezone.now()).total_seconds()
        minutos = int(tiempo_restante // 60)
        segundos = int(tiempo_restante % 60)
        mensaje = f'Cuenta bloqueada temporalmente. Intenta de nuevo en {minutos} minutos y {segundos} segundos.'
        return True, tiempo_restante, mensaje
    
    # Si el bloqueo expiró, resetear contador
    if usuario.bloqueado_hasta and usuario.bloqueado_hasta <= timezone.now():
        usuario.intentos_fallidos = 0
        usuario.bloqueado_hasta = None
        usuario.save()
    
    return False, 0, ''


def registrar_intento_fallido(usuario):
    """
    Registra un intento fallido de login y bloquea si es necesario
    
    Args:
        usuario: Instancia del modelo Usuario
        
    Returns:
        tuple: (esta_bloqueado, mensaje)
    """
    usuario.intentos_fallidos += 1
    usuario.ultimo_intento = timezone.now()
    
    # Bloquear después de 3 intentos fallidos por 15 minutos
    if usuario.intentos_fallidos >= 3:
        usuario.bloqueado_hasta = timezone.now() + timedelta(minutes=15)
        usuario.save()
        return True, 'Cuenta bloqueada temporalmente por 15 minutos debido a múltiples intentos fallidos.'
    
    usuario.save()
    intentos_restantes = 3 - usuario.intentos_fallidos
    return False, f'Credenciales incorrectas. Te quedan {intentos_restantes} intentos antes del bloqueo.'


def resetear_intentos(usuario):
    """
    Resetea el contador de intentos fallidos (cuando el login es exitoso)
    
    Args:
        usuario: Instancia del modelo Usuario
    """
    usuario.intentos_fallidos = 0
    usuario.bloqueado_hasta = None
    usuario.ultimo_intento = None
    usuario.save()


def validar_respuesta_secreta(respuesta):
    """
    Valida que la respuesta secreta no sea demasiado común o débil
    
    Args:
        respuesta: Respuesta secreta a validar
        
    Returns:
        tuple: (es_valida, mensaje_error)
    """
    if not respuesta or len(respuesta.strip()) < 3:
        return False, 'La respuesta secreta debe tener al menos 3 caracteres'
    
    # Respuestas comunes que deben ser rechazadas
    respuestas_comunes = [
        '123', '1234', '12345', '123456',
        'password', 'contraseña', 'password123',
        'admin', 'administrador',
        'test', 'prueba',
        'qwerty', 'abc123',
        'nombre', 'nombre123',
        'fecha', 'fecha123',
        'si', 'sí', 'no',
        'ninguna', 'nada'
    ]
    
    respuesta_lower = respuesta.lower().strip()
    
    if respuesta_lower in respuestas_comunes:
        return False, 'La respuesta secreta es demasiado común. Por favor, elige una respuesta más segura y personal.'
    
    # Verificar que no sea solo números
    if respuesta.strip().isdigit():
        return False, 'La respuesta secreta no puede ser solo números. Debe contener letras.'
    
    # Verificar que no sea solo letras repetidas
    if len(set(respuesta_lower)) <= 2:
        return False, 'La respuesta secreta es demasiado simple. Usa una combinación más compleja.'
    
    return True, ''


def es_respuesta_secreta_segura(respuesta):
    """
    Verifica si una respuesta secreta es segura (para uso en registro)
    
    Args:
        respuesta: Respuesta secreta a verificar
        
    Returns:
        bool: True si es segura
    """
    es_valida, _ = validar_respuesta_secreta(respuesta)
    return es_valida



