from django.contrib import admin
from .models import Barbero, ServicioBarbero

@admin.register(Barbero)
class BarberoAdmin(admin.ModelAdmin):
    list_display = ['usuario', 'activo', 'fecha_contratacion']
    list_filter = ['activo']
    search_fields = ['usuario__email', 'usuario__first_name', 'usuario__last_name']

@admin.register(ServicioBarbero)
class ServicioBarberoAdmin(admin.ModelAdmin):
    list_display = ['barbero', 'servicio', 'duracion_minutos', 'activo', 'fecha_actualizacion']
    list_filter = ['activo', 'servicio']
    search_fields = ['barbero__usuario__email', 'servicio__nombre']
