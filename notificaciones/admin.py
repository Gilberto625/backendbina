from django.contrib import admin
from .models import Notificacion, DispositivoFCM


@admin.register(Notificacion)
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'canal', 'tipo_evento', 'estado', 'fecha_creacion', 'fecha_enviada')
    list_filter = ('canal', 'estado', 'tipo_evento', 'fecha_creacion')
    search_fields = ('usuario__email', 'destinatario', 'asunto', 'mensaje')
    readonly_fields = ('fecha_creacion', 'fecha_enviada')
    ordering = ('-fecha_creacion',)


@admin.register(DispositivoFCM)
class DispositivoFCMAdmin(admin.ModelAdmin):
    list_display = ('id', 'usuario', 'plataforma', 'nombre_dispositivo', 'activo', 'fecha_registro', 'fecha_ultimo_uso')
    list_filter = ('plataforma', 'activo', 'fecha_registro')
    search_fields = ('usuario__email', 'nombre_dispositivo', 'token')
    readonly_fields = ('fecha_registro', 'fecha_ultimo_uso')
    ordering = ('-fecha_ultimo_uso',)
