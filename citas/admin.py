from django.contrib import admin
from .models import Cita, Servicio, Silla

@admin.register(Silla)
class SillaAdmin(admin.ModelAdmin):
    list_display = ['numero', 'nombre', 'activa']
    list_filter = ['activa']
    search_fields = ['nombre', 'numero']

@admin.register(Servicio)
class ServicioAdmin(admin.ModelAdmin):
    list_display = ['nombre', 'categoria', 'precio_base', 'duracion_minutos', 'activo']
    list_filter = ['categoria', 'activo']
    search_fields = ['nombre', 'descripcion']

@admin.register(Cita)
class CitaAdmin(admin.ModelAdmin):
    list_display = ['id', 'cliente', 'servicio', 'fecha_hora', 'estado', 'barbero', 'silla']
    list_filter = ['estado', 'fecha_hora', 'servicio']
    search_fields = ['cliente__email', 'cliente__username', 'notas']
    date_hierarchy = 'fecha_hora'
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion']
