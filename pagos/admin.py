from django.contrib import admin
from .models import Pago

@admin.register(Pago)
class PagoAdmin(admin.ModelAdmin):
    list_display = ['id', 'cliente', 'monto', 'metodo_pago', 'estado', 'cita', 'compra', 'fecha_creacion']
    list_filter = ['estado', 'metodo_pago', 'fecha_creacion']
    search_fields = ['cliente__email', 'id_operacion', 'mercado_pago_id']
    date_hierarchy = 'fecha_creacion'
    readonly_fields = ['fecha_creacion', 'fecha_actualizacion', 'fecha_completado', 'fecha_validacion']
