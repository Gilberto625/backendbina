from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import Usuario

@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    """
    Configuración del admin para el modelo Usuario
    Control de acceso: Solo staff y superusers pueden acceder
    """
    list_display = ['email', 'username', 'first_name', 'last_name', 'is_staff', 'is_superuser', 'verificado', 'is_active']
    list_filter = ['is_staff', 'is_superuser', 'verificado', 'is_active', 'date_joined']
    search_fields = ['email', 'username', 'first_name', 'last_name']
    ordering = ['email']
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Información Personal', {'fields': ('first_name', 'last_name', 'email', 'telefono')}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Seguridad', {'fields': ('verificado', 'totp_enabled', 'confirmado')}),
        ('Fechas Importantes', {'fields': ('last_login', 'date_joined')}),
    )
    
    def has_delete_permission(self, request, obj=None):
        """Solo superusuarios pueden eliminar usuarios"""
        return request.user.is_superuser
    
    def has_change_permission(self, request, obj=None):
        """Solo staff puede editar usuarios"""
        return request.user.is_staff
    
    def has_view_permission(self, request, obj=None):
        """Solo staff puede ver usuarios"""
        return request.user.is_staff
