# accounts/utils/password_verification.py
"""
Utilidades para verificar la seguridad de contraseñas
- Verificación de salts únicos
- Verificación de formato de hash
"""
from django.contrib.auth.hashers import check_password, is_password_usable
from django.contrib.auth import get_user_model

Usuario = get_user_model()


def verificar_salt_unico(usuario):
    """
    Verifica que la contraseña del usuario tenga un salt único
    
    Args:
        usuario: Instancia del modelo Usuario
        
    Returns:
        dict: Información sobre el hash y salt
    """
    if not usuario.password or not is_password_usable(usuario.password):
        return {
            'valido': False,
            'error': 'Contraseña no válida o no hasheada'
        }
    
    # Django almacena contraseñas en formato: algorithm$iterations$salt$hash
    partes = usuario.password.split('$')
    
    if len(partes) < 4:
        return {
            'valido': False,
            'error': 'Formato de hash inválido'
        }
    
    algoritmo = partes[0]
    iteraciones = partes[1] if len(partes) > 1 else None
    salt = partes[2] if len(partes) > 2 else None
    hash_value = partes[3] if len(partes) > 3 else None
    
    return {
        'valido': True,
        'algoritmo': algoritmo,
        'iteraciones': iteraciones,
        'salt': salt,
        'salt_length': len(salt) if salt else 0,
        'hash_length': len(hash_value) if hash_value else 0,
        'formato': f'{algoritmo}${iteraciones}${salt[:10]}...${hash_value[:20]}...'
    }


def verificar_contraseñas_sin_salt():
    """
    Verifica que todas las contraseñas en la base de datos tengan salts únicos
    
    Returns:
        dict: Resultado de la verificación
    """
    usuarios = Usuario.objects.all()
    resultados = {
        'total': usuarios.count(),
        'validos': 0,
        'invalidos': 0,
        'errores': []
    }
    
    salts_vistos = set()
    
    for usuario in usuarios:
        if not usuario.password:
            resultados['invalidos'] += 1
            resultados['errores'].append({
                'usuario': usuario.email,
                'error': 'Sin contraseña'
            })
            continue
        
        info = verificar_salt_unico(usuario)
        
        if not info['valido']:
            resultados['invalidos'] += 1
            resultados['errores'].append({
                'usuario': usuario.email,
                'error': info.get('error', 'Desconocido')
            })
        else:
            resultados['validos'] += 1
            salt = info.get('salt', '')
            
            # Verificar que el salt sea único
            if salt in salts_vistos:
                resultados['errores'].append({
                    'usuario': usuario.email,
                    'advertencia': 'Salt duplicado detectado (poco probable pero posible)'
                })
            else:
                salts_vistos.add(salt)
    
    return resultados


def verificar_contraseña_texto_plano():
    """
    Verifica que no haya contraseñas en texto plano en la base de datos
    
    Returns:
        dict: Resultado de la verificación
    """
    usuarios = Usuario.objects.all()
    resultados = {
        'total': usuarios.count(),
        'texto_plano': [],
        'hasheadas': 0
    }
    
    # Patrones que indican texto plano (contraseñas comunes)
    patrones_texto_plano = [
        'password', '123456', 'admin', 'test', 'qwerty'
    ]
    
    for usuario in usuarios:
        if not usuario.password:
            continue
        
        # Verificar si es un hash válido de Django
        if not is_password_usable(usuario.password):
            resultados['texto_plano'].append({
                'usuario': usuario.email,
                'password': usuario.password[:20] + '...' if len(usuario.password) > 20 else usuario.password
            })
        else:
            # Verificar que no sea una contraseña común en texto plano
            password_lower = usuario.password.lower()
            if any(patron in password_lower for patron in patrones_texto_plano):
                # Si tiene el formato de hash, está bien
                if '$' not in usuario.password:
                    resultados['texto_plano'].append({
                        'usuario': usuario.email,
                        'advertencia': 'Posible contraseña en texto plano'
                    })
                else:
                    resultados['hasheadas'] += 1
            else:
                resultados['hasheadas'] += 1
    
    return resultados

