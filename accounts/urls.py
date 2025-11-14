# accounts/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # Autenticación básica
    path('csrf/', views.get_csrf_token, name='csrf_token'),  # Para Angular
    path('register/', views.register_user, name='register'),
    path('register/2fa/verificar/', views.verificar_registro_2fa, name='verificar_2fa'),
    path('login/', views.login_user, name='login'),
    path('login/2fa/verificar/', views.verificar_login_2fa, name='verificar_login_2fa'),
    path('login/2fa/solicitar-codigo/', views.solicitar_codigo_email, name='solicitar_codigo_email'),
    path('login/google/', views.google_login, name='google_login'),

    # Recuperación de contraseña (preguntas secretas - método antiguo)
    path('recuperar/', views.recuperar_contrasena, name='recuperar_contrasena'),
    path('restablecer/', views.restablecer_contrasena, name='restablecer_contrasena'),

    # Recuperación de contraseña por email (nuevo método)
    path('recuperar/email/', views.solicitar_recuperacion_email, name='solicitar_recuperacion_email'),
    path('restablecer/email/', views.restablecer_con_token_email, name='restablecer_con_token_email'),

    # TOTP (Google Authenticator)
    path('totp/configurar/', views.configurar_totp, name='configurar_totp'),
    path('totp/habilitar/', views.verificar_habilitar_totp, name='verificar_habilitar_totp'),
    path('totp/verificar/', views.verificar_totp_login, name='verificar_totp_login'),

    # Códigos de respaldo
    path('backup-codes/generar/', views.generar_codigos_respaldo, name='generar_codigos_respaldo'),

    # Estado de seguridad
    path('seguridad/estado/', views.verificar_estado_seguridad, name='verificar_estado_seguridad'),
]