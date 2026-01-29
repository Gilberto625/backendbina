# notificaciones/urls.py
from django.urls import path
from . import views

app_name = 'notificaciones'

urlpatterns = [
    # Endpoints para usuarios
    path('mis-notificaciones/', views.mis_notificaciones, name='mis_notificaciones'),
    
    # Endpoints para dispositivos FCM (push notifications)
    path('dispositivos/registrar/', views.registrar_dispositivo_fcm, name='registrar_dispositivo_fcm'),
    path('dispositivos/eliminar/', views.eliminar_dispositivo_fcm, name='eliminar_dispositivo_fcm'),
    path('dispositivos/', views.listar_dispositivos_fcm, name='listar_dispositivos_fcm'),
    
    # Endpoints para admin/secretaria
    path('enviar/', views.enviar_notificacion, name='enviar_notificacion'),
    path('historial/', views.historial_notificaciones, name='historial_notificaciones'),
    path('citas/<int:cita_id>/recordatorio/', views.programar_recordatorio_cita, name='programar_recordatorio_cita'),
    path('procesar-programadas/', views.procesar_notificaciones_programadas, name='procesar_notificaciones_programadas'),
]
