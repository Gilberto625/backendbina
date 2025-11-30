# accounts/utils/logger.py
"""
Sistema de logging seguro que no expone información sensible
"""
import logging
import re

logger = logging.getLogger('accounts')


def sanitize_log_data(data):
    """
    Remueve información sensible de los datos antes de registrar
    
    Args:
        data: Diccionario o string con datos a sanitizar
        
    Returns:
        Datos sanitizados sin información sensible
    """
    if isinstance(data, dict):
        sanitized = data.copy()
        sensitive_fields = [
            'password', 'contrasena', 'token', 'secret', 
            'api_key', 'apikey', 'auth', 'authorization',
            'csrf', 'session', 'cookie'
        ]
        
        for field in sensitive_fields:
            # Buscar en todas las claves (case insensitive)
            for key in list(sanitized.keys()):
                if field.lower() in key.lower():
                    sanitized[key] = '***REDACTED***'
        
        return sanitized
    
    if isinstance(data, str):
        # Remover posibles contraseñas o tokens en strings
        # Patrón para detectar posibles tokens/contraseñas
        patterns = [
            r'password["\']?\s*[:=]\s*["\']?([^"\']+)',
            r'contrasena["\']?\s*[:=]\s*["\']?([^"\']+)',
            r'token["\']?\s*[:=]\s*["\']?([^"\']+)',
        ]
        
        sanitized = data
        for pattern in patterns:
            sanitized = re.sub(pattern, r'***REDACTED***', sanitized, flags=re.IGNORECASE)
        
        return sanitized
    
    return data


def log_info(message, data=None):
    """
    Registra información de forma segura
    
    Args:
        message: Mensaje a registrar
        data: Datos opcionales (serán sanitizados)
    """
    if data:
        data = sanitize_log_data(data)
        logger.info(f"{message} - Data: {data}")
    else:
        logger.info(message)


def log_error(message, error=None, data=None):
    """
    Registra errores de forma segura
    
    Args:
        message: Mensaje de error
        error: Excepción opcional
        data: Datos opcionales (serán sanitizados)
    """
    if data:
        data = sanitize_log_data(data)
    
    if error:
        logger.error(f"{message} - Error: {str(error)} - Data: {data}", exc_info=True)
    else:
        logger.error(f"{message} - Data: {data}")


def log_security_event(event_type, user_id=None, ip_address=None, details=None):
    """
    Registra eventos de seguridad de forma segura
    
    Args:
        event_type: Tipo de evento (login_failed, account_locked, etc.)
        user_id: ID del usuario (opcional)
        ip_address: Dirección IP (opcional)
        details: Detalles adicionales (serán sanitizados)
    """
    log_data = {
        'event': event_type,
        'user_id': user_id,
        'ip': ip_address,
    }
    
    if details:
        log_data['details'] = sanitize_log_data(details)
    
    logger.warning(f"SECURITY EVENT: {event_type} - {log_data}")


