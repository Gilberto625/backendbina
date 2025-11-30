"""
Middleware personalizado para headers de seguridad HTTP
"""
from django.utils.deprecation import MiddlewareMixin


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Middleware para agregar headers de seguridad HTTP
    """
    
    def process_response(self, request, response):
        # Solo agregar headers en producción (HTTPS)
        if request.is_secure() or not request.get_host().startswith('localhost'):
            # Strict-Transport-Security (HSTS)
            if not response.get('Strict-Transport-Security'):
                response['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains; preload'
            
            # X-Frame-Options
            if not response.get('X-Frame-Options'):
                response['X-Frame-Options'] = 'DENY'
            
            # X-Content-Type-Options
            if not response.get('X-Content-Type-Options'):
                response['X-Content-Type-Options'] = 'nosniff'
            
            # X-XSS-Protection
            if not response.get('X-XSS-Protection'):
                response['X-XSS-Protection'] = '1; mode=block'
            
            # Content-Security-Policy
            if not response.get('Content-Security-Policy'):
                response['Content-Security-Policy'] = (
                    "default-src 'self'; "
                    "script-src 'self' 'unsafe-inline' https://www.gstatic.com https://www.googleapis.com https://apis.google.com; "
                    "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com; "
                    "img-src 'self' data: https:; "
                    "font-src 'self' data: https://fonts.gstatic.com; "
                    "connect-src 'self' https://backendbina-1.onrender.com https://frontbina.vercel.app https://*.vercel.app https://www.googleapis.com; "
                    "frame-ancestors 'none'; "
                    "base-uri 'self'; "
                    "form-action 'self';"
                )
            
            # Referrer-Policy
            if not response.get('Referrer-Policy'):
                response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            
            # Permissions-Policy (anteriormente Feature-Policy)
            if not response.get('Permissions-Policy'):
                response['Permissions-Policy'] = (
                    "geolocation=(), "
                    "microphone=(), "
                    "camera=(), "
                    "payment=(), "
                    "usb=(), "
                    "magnetometer=(), "
                    "gyroscope=(), "
                    "speaker=()"
                )
        
        return response

