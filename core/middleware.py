"""
Middleware personalizado para headers de seguridad HTTP
"""
from django.utils.deprecation import MiddlewareMixin


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Middleware para agregar headers de seguridad HTTP
    IMPORTANTE: Agrega headers en TODAS las respuestas, incluyendo errores
    """
    
    def process_response(self, request, response):
        # Agregar headers en TODAS las respuestas (incluyendo errores 4xx, 5xx)
        # Solo verificar HTTPS en producción (no en localhost)
        is_production = not request.get_host().startswith('localhost') and not request.get_host().startswith('127.0.0.1')
        
        # Agregar headers siempre, incluso en respuestas de error
        # Esto es crítico para seguridad
        
        # Strict-Transport-Security (HSTS) - Solo en HTTPS
        if (request.is_secure() or is_production) and not response.get('Strict-Transport-Security'):
            response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
        
        # X-Frame-Options - Siempre
        if not response.get('X-Frame-Options'):
            response['X-Frame-Options'] = 'DENY'
        
        # X-Content-Type-Options - Siempre
        if not response.get('X-Content-Type-Options'):
            response['X-Content-Type-Options'] = 'nosniff'
        
        # X-XSS-Protection - Siempre
        if not response.get('X-XSS-Protection'):
            response['X-XSS-Protection'] = '1; mode=block'
        
            # Content-Security-Policy - Mejorado sin 'unsafe-inline' en script-src
            # Para APIs REST, no necesitamos 'unsafe-inline' ya que no servimos HTML con scripts inline
            # Incluimos dominios de Firebase para compatibilidad con OAuth2.0
            if not response.get('Content-Security-Policy'):
                # CSP más restrictivo para API backend
                # No permitimos scripts inline ya que es una API REST
                # Incluimos Firebase para OAuth2.0 con Google
                response['Content-Security-Policy'] = (
                    "default-src 'self'; "
                    "script-src 'self' https://www.gstatic.com https://www.googleapis.com https://apis.google.com https://*.firebaseapp.com; "
                    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "  # CSS inline puede ser necesario
                    "img-src 'self' data: https: https://*.googleusercontent.com; "
                    "font-src 'self' data: https://fonts.gstatic.com; "
                    "connect-src 'self' https://backendbina-1.onrender.com https://frontbina.vercel.app https://*.vercel.app https://www.googleapis.com https://*.googleapis.com https://*.firebaseapp.com https://*.firebaseio.com https://identitytoolkit.googleapis.com https://securetoken.googleapis.com; "
                    "frame-src 'self' https://*.firebaseapp.com https://accounts.google.com; "
                    "frame-ancestors 'none'; "
                    "base-uri 'self'; "
                    "form-action 'self'; "
                    "object-src 'none'; "  # Prevenir plugins
                    "upgrade-insecure-requests;"  # Forzar HTTPS
                )
        
        # Referrer-Policy - Siempre
        if not response.get('Referrer-Policy'):
            response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        
        # Permissions-Policy (anteriormente Feature-Policy) - Siempre
        if not response.get('Permissions-Policy'):
            response['Permissions-Policy'] = (
                "geolocation=(), "
                "microphone=(), "
                "camera=(), "
                "payment=(), "
                "usb=(), "
                "magnetometer=(), "
                "gyroscope=(), "
                "speaker=(), "
                "autoplay=(), "
                "fullscreen=(self)"
            )
        
        return response


