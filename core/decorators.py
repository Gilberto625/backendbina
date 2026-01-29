# core/decorators.py
"""
Decoradores para verificación de roles y permisos en endpoints
"""
from functools import wraps
from django.http import JsonResponse
from django.contrib.auth import get_user_model

Usuario = get_user_model()


def obtener_usuario_autenticado(request):
    """
    Obtiene el usuario autenticado desde la sesión o token
    Retorna None si no está autenticado
    """
    if hasattr(request, 'user') and request.user.is_authenticated:
        return request.user
    return None


def requiere_autenticacion(view_func):
    """
    Decorador que verifica que el usuario esté autenticado
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        usuario = obtener_usuario_autenticado(request)
        if not usuario:
            return JsonResponse({
                'error': 'Autenticación requerida',
                'mensaje': 'Debes iniciar sesión para acceder a este recurso'
            }, status=401)
        
        # Agregar usuario al request para uso en la vista
        request.usuario_autenticado = usuario
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view


def requiere_rol(*roles_permitidos):
    """
    Decorador que verifica que el usuario tenga uno de los roles especificados
    
    Uso:
        @requiere_rol('administrador', 'secretaria')
        def mi_vista(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            usuario = obtener_usuario_autenticado(request)
            
            if not usuario:
                return JsonResponse({
                    'error': 'Autenticación requerida',
                    'mensaje': 'Debes iniciar sesión para acceder a este recurso'
                }, status=401)
            
            # Verificar que el usuario tenga uno de los roles permitidos
            if usuario.rol not in roles_permitidos:
                return JsonResponse({
                    'error': 'Acceso denegado',
                    'mensaje': f'No tienes permisos para acceder a este recurso. Roles requeridos: {", ".join(roles_permitidos)}'
                }, status=403)
            
            # Agregar usuario al request
            request.usuario_autenticado = usuario
            return view_func(request, *args, **kwargs)
        
        return _wrapped_view
    return decorator


# Decoradores específicos para cada rol
def requiere_cliente(view_func):
    """Decorador que verifica que el usuario sea Cliente"""
    return requiere_rol('cliente')(view_func)


def requiere_secretaria(view_func):
    """Decorador que verifica que el usuario sea Secretaria"""
    return requiere_rol('secretaria')(view_func)


def requiere_barbero(view_func):
    """Decorador que verifica que el usuario sea Barbero"""
    return requiere_rol('barbero')(view_func)


def requiere_administrador(view_func):
    """Decorador que verifica que el usuario sea Administrador"""
    return requiere_rol('administrador')(view_func)


def requiere_staff(view_func):
    """
    Decorador que verifica que el usuario sea parte del staff
    (Secretaria, Barbero o Administrador)
    """
    return requiere_rol('secretaria', 'barbero', 'administrador')(view_func)


def requiere_admin_o_secretaria(view_func):
    """
    Decorador que verifica que el usuario sea Administrador o Secretaria
    Útil para funciones administrativas
    """
    return requiere_rol('administrador', 'secretaria')(view_func)


def permite_invitado(view_func):
    """
    Decorador que permite acceso tanto a usuarios autenticados como invitados
    El usuario autenticado (si existe) se agrega al request
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        usuario = obtener_usuario_autenticado(request)
        request.usuario_autenticado = usuario  # Puede ser None
        return view_func(request, *args, **kwargs)
    
    return _wrapped_view
