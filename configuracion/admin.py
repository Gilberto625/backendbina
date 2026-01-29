from django.contrib import admin
from .models import ConfiguracionSistema

@admin.register(ConfiguracionSistema)
class ConfiguracionSistemaAdmin(admin.ModelAdmin):
    list_display = ['dia_semana', 'demanda', 'dias_anticipacion_alta', 'dias_anticipacion_baja', 'fecha_actualizacion']
    list_filter = ['demanda']
    list_editable = ['demanda', 'dias_anticipacion_alta', 'dias_anticipacion_baja']
