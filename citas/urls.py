# citas/urls.py
from django.urls import path
from . import views

app_name = 'citas'

urlpatterns = [
    # Endpoints públicos
    path('servicios/', views.listar_servicios, name='listar_servicios'),
    path('barberos/', views.listar_barberos, name='listar_barberos'),
    path('sillas-disponibles/', views.sillas_disponibles, name='sillas_disponibles'),
    path('disponibilidad/', views.consultar_disponibilidad, name='consultar_disponibilidad'),
    
    # Endpoints para clientes
    path('crear/', views.crear_cita, name='crear_cita'),
    path('mis-citas/', views.mis_citas, name='mis_citas'),
    path('<int:cita_id>/', views.detalle_cita, name='detalle_cita'),
    path('<int:cita_id>/cancelar/', views.cancelar_cita, name='cancelar_cita'),
    
    # Endpoints para secretaria/admin
    path('agenda/', views.agenda_completa, name='agenda_completa'),
    path('crear-manual/', views.crear_cita_manual, name='crear_cita_manual'),
    path('<int:cita_id>/asistencia/', views.registrar_asistencia, name='registrar_asistencia'),
]
