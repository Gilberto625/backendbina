# accounts/urls.py
from django.urls import path
from . import views
from . import admin_views

urlpatterns = [
    # ============================================
    # AUTENTICACIÓN
    # ============================================
    path('csrf/', views.get_csrf_token, name='csrf_token'),
    path('register/', views.register_user, name='register'),
    path('register/2fa/verificar/', views.verificar_registro_2fa, name='verificar_2fa'),
    path('login/', views.login_user, name='login'),
    path('login/2fa/verificar/', views.verificar_login_2fa, name='verificar_login_2fa'),
    path('login/google/', views.google_login, name='google_login'),
    path('recuperar/', views.recuperar_contrasena, name='recuperar_contrasena'),
    path('recuperar-otp/', views.recuperar_otp, name='recuperar_otp'),
    path('verificar-otp-recuperacion/', views.verificar_otp_recuperacion, name='verificar_otp_recuperacion'),
    path('reenviar-otp-recuperacion/', views.reenviar_otp_recuperacion, name='reenviar_otp_recuperacion'),
    path('actualizar-contrasena-otp/', views.actualizar_contrasena_otp, name='actualizar_contrasena_otp'),
    path('restablecer/', views.restablecer_contrasena, name='restablecer_contrasena'),
    
    # ============================================
    # ADMIN - DASHBOARD & REPORTES
    # ============================================
    path('admin/dashboard/', admin_views.dashboard_stats, name='admin_dashboard'),
    path('admin/reportes/', admin_views.reportes, name='admin_reportes'),
    path('admin/configuracion/', admin_views.configuracion, name='admin_configuracion'),
    
    # ============================================
    # ADMIN - SERVICIOS
    # ============================================
    path('admin/servicios/', admin_views.servicios_list, name='admin_servicios_list'),
    path('admin/servicios/<int:servicio_id>/', admin_views.servicio_detail, name='admin_servicio_detail'),
    
    # ============================================
    # ADMIN - PRODUCTOS
    # ============================================
    path('admin/productos/', admin_views.productos_list, name='admin_productos_list'),
    path('admin/productos/<int:producto_id>/', admin_views.producto_detail, name='admin_producto_detail'),
    path('admin/productos/<int:producto_id>/stock/', admin_views.producto_stock, name='admin_producto_stock'),
    
    # ============================================
    # ADMIN - EMPLEADOS
    # ============================================
    path('admin/empleados/', admin_views.empleados_list, name='admin_empleados_list'),
    path('admin/empleados/<int:empleado_id>/', admin_views.empleado_detail, name='admin_empleado_detail'),
    
    # ============================================
    # ADMIN - IMÁGENES (Cloudinary)
    # ============================================
    path('admin/upload/', admin_views.upload_image, name='admin_upload_image'),
    path('admin/delete-image/', admin_views.delete_image, name='admin_delete_image'),
    
    # ============================================
    # PÚBLICAS - CATÁLOGOS (sin auth)
    # ============================================
    path('servicios/', admin_views.servicios_list, name='servicios_publicos'),
    path('productos/', admin_views.productos_list, name='productos_publicos'),
]