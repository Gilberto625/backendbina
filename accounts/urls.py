# accounts/urls.py
from django.urls import path
from . import views

urlpatterns = [
    # CSRF
    path('csrf/', views.get_csrf_token, name='csrf_token'),

    # Registro y verificación
    path('register/', views.register_user, name='register'),
    path('register/2fa/verificar/', views.verificar_registro_2fa, name='verificar_2fa'),

    # Login y logout
    path('login/', views.login_user, name='login'),
    path('login/2fa/verificar/', views.verificar_login_2fa, name='verificar_login_2fa'),
    path('login/google/', views.google_login, name='google_login'),
    path('logout/', views.logout_user, name='logout'),

    # Recuperación de contraseña
    path('obtener-pregunta-secreta/', views.obtener_pregunta_secreta, name='obtener_pregunta_secreta'),
    path('recuperar/', views.recuperar_contrasena, name='recuperar_contrasena'),
    path('restablecer/', views.restablecer_contrasena, name='restablecer_contrasena'),

    # OTP con SendGrid
    path('reenviar-otp/', views.reenviar_otp, name='reenviar_otp'),
    path('recuperar-otp/', views.solicitar_recuperacion_otp, name='recuperar_otp'),
    path('verificar-otp-recuperacion/', views.verificar_otp_recuperacion, name='verificar_otp_recuperacion'),
    path('actualizar-contrasena-otp/', views.actualizar_contrasena_otp, name='actualizar_contrasena_otp'),

    # Gestión de seguridad
    path('seguridad/estado/', views.obtener_estado_seguridad, name='obtener_estado_seguridad'),
    path('cambiar-contrasena/', views.cambiar_contrasena, name='cambiar_contrasena'),
    path('backup-codes/generar/', views.generar_codigos_respaldo, name='generar_codigos_respaldo'),
]