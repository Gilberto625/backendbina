# accounts/utils/validators.py
"""
Utilidades para validación y sanitización de datos de entrada
Protección contra XSS, SQL injection y validación de contraseñas
"""
import re
import html
from django.core.exceptions import ValidationError


def sanitize_string(value: str, max_length: int = None) -> str:
    """
    Sanitiza una cadena de texto para prevenir XSS y SQL injection
    
    Args:
        value: Cadena a sanitizar
        max_length: Longitud máxima permitida
        
    Returns:
        Cadena sanitizada
    """
    if not isinstance(value, str):
        return str(value)
    
    # Escapar caracteres HTML para prevenir XSS
    sanitized = html.escape(value)
    
    # Remover caracteres peligrosos para SQL injection
    # Django ORM ya protege contra SQL injection, pero esto es una capa adicional
    dangerous_chars = ["'", '"', ';', '--', '/*', '*/', 'xp_', 'sp_']
    for char in dangerous_chars:
        sanitized = sanitized.replace(char, '')
    
    # Limitar longitud si se especifica
    if max_length and len(sanitized) > max_length:
        sanitized = sanitized[:max_length]
    
    return sanitized.strip()


def validate_email(email: str) -> bool:
    """
    Valida formato de email
    
    Args:
        email: Email a validar
        
    Returns:
        True si es válido, False en caso contrario
    """
    if not email or not isinstance(email, str):
        return False
    
    # Patrón básico de email
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_phone(phone: str) -> bool:
    """
    Valida formato de teléfono (solo números, guiones y espacios)
    
    Args:
        phone: Teléfono a validar
        
    Returns:
        True si es válido, False en caso contrario
    """
    if not phone or not isinstance(phone, str):
        return False
    
    # Solo números, espacios, guiones y paréntesis
    pattern = r'^[\d\s\-\(\)]+$'
    return bool(re.match(pattern, phone)) and len(phone.replace(' ', '').replace('-', '').replace('(', '').replace(')', '')) >= 8


def validate_password_strength(password: str):
    """
    Valida la complejidad de una contraseña
    
    Requisitos:
    - Mínimo 8 caracteres
    - Al menos una letra mayúscula
    - Al menos una letra minúscula
    - Al menos un número
    - Al menos un carácter especial
    
    Args:
        password: Contraseña a validar
        
    Returns:
        Tupla (es_válida, mensaje_error)
    """
    if not password or not isinstance(password, str):
        return False, 'La contraseña es requerida'
    
    errors = []
    
    # Longitud mínima
    if len(password) < 8:
        errors.append('al menos 8 caracteres')
    
    # Mayúscula
    if not re.search(r'[A-Z]', password):
        errors.append('una letra mayúscula')
    
    # Minúscula
    if not re.search(r'[a-z]', password):
        errors.append('una letra minúscula')
    
    # Número
    if not re.search(r'\d', password):
        errors.append('un número')
    
    # Carácter especial
    if not re.search(r'[!@#$%^&*()_+\-=\[\]{};\':"\\|,.<>\/?]', password):
        errors.append('un carácter especial (!@#$%^&*()_+-=[]{}|;:,.<>?)')
    
    if errors:
        mensaje = f'La contraseña debe contener: {", ".join(errors)}'
        return False, mensaje
    
    return True, ''


def sanitize_user_input(data: dict) -> dict:
    """
    Sanitiza todos los campos de entrada del usuario
    
    Args:
        data: Diccionario con datos del usuario
        
    Returns:
        Diccionario con datos sanitizados
    """
    sanitized = {}
    
    # Campos de texto que necesitan sanitización
    text_fields = ['nombre', 'apellidopaterno', 'apellidomaterno', 'username', 
                   'correo', 'telefono', 'preguntasecreta', 'respuestasecreta']
    
    for field in text_fields:
        if field in data and data[field]:
            if field == 'correo':
                # Email se sanitiza pero también se valida
                sanitized[field] = sanitize_string(data[field], max_length=254)
            elif field == 'telefono':
                sanitized[field] = sanitize_string(data[field], max_length=15)
            elif field == 'username':
                sanitized[field] = sanitize_string(data[field], max_length=150)
            else:
                sanitized[field] = sanitize_string(data[field], max_length=255)
    
    # Campos que no necesitan sanitización (se validan por separado)
    if 'contrasena' in data:
        sanitized['contrasena'] = data['contrasena']  # No sanitizar, solo validar
    
    return sanitized


def validate_registration_data(data: dict) -> tuple[bool, str]:
    """
    Valida todos los datos de registro
    
    Args:
        data: Diccionario con datos de registro
        
    Returns:
        Tupla (es_válido, mensaje_error)
    """
    # Validar campos requeridos
    required_fields = ['nombre', 'apellidopaterno', 'apellidomaterno', 'username',
                      'correo', 'contrasena', 'telefono', 'preguntasecreta', 'respuestasecreta']
    
    for field in required_fields:
        if not data.get(field):
            return False, f'El campo {field} es obligatorio'
    
    # Validar email
    if not validate_email(data['correo']):
        return False, 'El formato del correo electrónico no es válido'
    
    # Validar teléfono
    if not validate_phone(data['telefono']):
        return False, 'El formato del teléfono no es válido'
    
    # Validar username (solo letras, números y guiones bajos)
    username = data.get('username', '')
    if not re.match(r'^[a-zA-Z0-9_]+$', username):
        return False, 'El nombre de usuario solo puede contener letras, números y guiones bajos'
    
    if len(username) < 3:
        return False, 'El nombre de usuario debe tener al menos 3 caracteres'
    
    # Validar contraseña
    is_valid, error_msg = validate_password_strength(data['contrasena'])
    if not is_valid:
        return False, error_msg
    
    return True, ''

