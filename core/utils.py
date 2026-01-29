# core/utils.py
"""
Utilidades generales para el sistema
"""
from django.contrib.auth import get_user_model
from django.http import JsonResponse

Usuario = get_user_model()


def obtener_usuario_desde_request(request):
    """
    Obtiene el usuario autenticado desde el request
    Retorna None si no está autenticado
    """
    if hasattr(request, 'usuario_autenticado'):
        return request.usuario_autenticado
    
    if hasattr(request, 'user') and request.user.is_authenticated:
        return request.user
    
    return None


def respuesta_error(mensaje, codigo=400, detalles=None):
    """
    Crea una respuesta JSON de error estandarizada
    """
    respuesta = {
        'error': mensaje,
        'ok': False
    }
    if detalles:
        respuesta['detalles'] = detalles
    
    return JsonResponse(respuesta, status=codigo)


def respuesta_exito(mensaje, datos=None, codigo=200):
    """
    Crea una respuesta JSON de éxito estandarizada
    """
    respuesta = {
        'ok': True,
        'mensaje': mensaje
    }
    if datos:
        respuesta.update(datos)
    
    return JsonResponse(respuesta, status=codigo)


def validar_rol_usuario(usuario, roles_permitidos):
    """
    Valida que el usuario tenga uno de los roles permitidos
    Retorna (True, None) si es válido, (False, mensaje_error) si no
    """
    if not usuario:
        return False, 'Usuario no autenticado'
    
    if usuario.rol not in roles_permitidos:
        return False, f'Rol no permitido. Roles requeridos: {", ".join(roles_permitidos)}'
    
    return True, None


def serializar_usuario(usuario, campos_adicionales=None):
    """
    Serializa un usuario a diccionario para respuestas JSON
    """
    if not usuario:
        return None
    
    datos = {
        'id': usuario.id,
        'email': usuario.email,
        'username': usuario.username,
        'first_name': usuario.first_name,
        'last_name': usuario.last_name,
        'rol': usuario.rol,
        'rol_display': usuario.get_rol_display(),
        'telefono': usuario.telefono,
        'verificado': usuario.verificado,
        'activo': usuario.activo,
    }
    
    if campos_adicionales:
        for campo in campos_adicionales:
            if hasattr(usuario, campo):
                datos[campo] = getattr(usuario, campo)
    
    return datos
