# core/middleware.py
"""
Middleware personalizado para el sistema
"""
from django.utils.deprecation import MiddlewareMixin
from django.contrib.auth import get_user_model

Usuario = get_user_model()


class UsuarioAutenticadoMiddleware(MiddlewareMixin):
    """
    Middleware que agrega el usuario autenticado al request
    para facilitar el acceso en las vistas
    """
    def process_request(self, request):
        # Django ya maneja request.user, pero podemos agregar una referencia adicional
        if hasattr(request, 'user') and request.user.is_authenticated:
            request.usuario_autenticado = request.user
        else:
            request.usuario_autenticado = None
        
        return None
