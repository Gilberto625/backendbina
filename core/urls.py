# core/urls.py
from django.contrib import admin
from django.urls import path, include, re_path
from django.views.generic import RedirectView

# Documentación API con drf-yasg
try:
    from rest_framework import permissions
    from drf_yasg.views import get_schema_view
    from drf_yasg import openapi
    
    schema_view = get_schema_view(
        openapi.Info(
            title="Barbería API",
            default_version='v1',
            description="API para el sistema de gestión de barbería",
            terms_of_service="https://www.google.com/policies/terms/",
            contact=openapi.Contact(email="contact@barberia.local"),
            license=openapi.License(name="BSD License"),
        ),
        public=True,
        permission_classes=(permissions.AllowAny,),
    )
    
    # URLs de documentación
    urlpatterns = [
        path('admin/', admin.site.urls),
        # Documentación API
        re_path(r'^swagger(?P<format>\.json|\.yaml)$', schema_view.without_ui(cache_timeout=0), name='schema-json'),
        re_path(r'^swagger/$', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
        re_path(r'^redoc/$', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
        # API endpoints
        path('api/usuarios/', include('accounts.urls')),
        path('api/citas/', include('citas.urls')),
        path('api/productos/', include('productos.urls')),
        path('api/pagos/', include('pagos.urls')),
        path('api/barberos/', include('barberos.urls')),
        path('api/notificaciones/', include('notificaciones.urls')),
        path('api/', include('configuracion.urls')),
        path('', RedirectView.as_view(url='/swagger/', permanent=False)),
    ]
except ImportError:
    # Si drf-yasg no está instalado, usar URLs sin documentación
    urlpatterns = [
        path('admin/', admin.site.urls),
        path('api/usuarios/', include('accounts.urls')),
        path('api/citas/', include('citas.urls')),
        path('api/productos/', include('productos.urls')),
        path('api/pagos/', include('pagos.urls')),
        path('api/barberos/', include('barberos.urls')),
        path('api/notificaciones/', include('notificaciones.urls')),
        path('api/', include('configuracion.urls')),
    ]
