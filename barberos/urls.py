# barberos/urls.py
from django.urls import path
from . import views

app_name = 'barberos'

urlpatterns = [
    # Endpoints públicos
    path('', views.listar_barberos, name='listar_barberos'),
    path('<int:barbero_id>/', views.detalle_barbero, name='detalle_barbero'),
    path('<int:barbero_id>/servicios/', views.servicios_barbero, name='servicios_barbero'),
    path('<int:barbero_id>/disponibilidad/', views.disponibilidad_barbero, name='disponibilidad_barbero'),
    
    # Endpoints para admin
    path('crear/', views.crear_barbero, name='crear_barbero'),
    path('<int:barbero_id>/actualizar/', views.actualizar_barbero, name='actualizar_barbero'),
    
    # Endpoints para admin/secretaria
    path('<int:barbero_id>/servicios/asignar/', views.asignar_servicio_barbero, name='asignar_servicio_barbero'),
    path('<int:barbero_id>/servicios/<int:servicio_id>/desactivar/', views.desactivar_servicio_barbero, name='desactivar_servicio_barbero'),
    path('<int:barbero_id>/citas/', views.citas_barbero, name='citas_barbero'),

    # Endpoints para barbero (autenticado)
    path('mis-servicios/', views.mis_servicios, name='mis_servicios'),
    path('mis-servicios/<int:servicio_id>/duracion/', views.actualizar_duracion_servicio, name='actualizar_duracion_servicio'),
    path('mis-citas/', views.mis_citas, name='mis_citas'),
]
