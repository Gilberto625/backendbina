# configuracion/urls.py
from django.urls import path
from . import views

app_name = 'configuracion'

urlpatterns = [
    # Endpoints de administración
    path('admin/metricas/', views.metricas, name='metricas'),
    path('admin/reportes/', views.reportes_financieros, name='reportes_financieros'),
    path('admin/dias/clasificar/', views.clasificar_dia_demanda, name='clasificar_dia_demanda'),
    path('admin/empleados/', views.listar_empleados, name='listar_empleados'),
    path('admin/empleados/crear/', views.crear_empleado, name='crear_empleado'),
    path('admin/empleados/<int:empleado_id>/', views.actualizar_empleado, name='actualizar_empleado'),
    path('admin/configuracion/', views.obtener_configuracion, name='obtener_configuracion'),
    path('admin/configuracion/actualizar/', views.actualizar_configuracion, name='actualizar_configuracion'),
]
