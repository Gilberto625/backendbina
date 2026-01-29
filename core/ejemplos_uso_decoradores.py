# core/ejemplos_uso_decoradores.py
"""
Ejemplos de uso de los decoradores de permisos
Este archivo es solo para referencia, no se ejecuta
"""

from core.decorators import (
    requiere_autenticacion,
    requiere_cliente,
    requiere_secretaria,
    requiere_barbero,
    requiere_administrador,
    requiere_staff,
    requiere_admin_o_secretaria,
    requiere_rol,
    permite_invitado
)
from core.utils import respuesta_exito, obtener_usuario_desde_request
from django.http import JsonResponse


# ============================================
# EJEMPLO 1: Endpoint solo para clientes
# ============================================
@requiere_cliente
def mi_cita_cliente(request):
    """Solo clientes pueden acceder"""
    usuario = obtener_usuario_desde_request(request)
    return respuesta_exito('Acceso permitido', {'usuario': usuario.email})


# ============================================
# EJEMPLO 2: Endpoint para secretaria o admin
# ============================================
@requiere_admin_o_secretaria
def gestionar_citas(request):
    """Solo secretaria o administrador"""
    usuario = obtener_usuario_desde_request(request)
    return respuesta_exito('Puedes gestionar citas')


# ============================================
# EJEMPLO 3: Endpoint para cualquier rol autenticado
# ============================================
@requiere_autenticacion
def perfil_usuario(request):
    """Cualquier usuario autenticado puede ver su perfil"""
    usuario = obtener_usuario_desde_request(request)
    return respuesta_exito('Perfil', {'rol': usuario.rol})


# ============================================
# EJEMPLO 4: Endpoint con múltiples roles permitidos
# ============================================
@requiere_rol('cliente', 'secretaria')
def ver_citas(request):
    """Clientes y secretarias pueden ver citas"""
    usuario = obtener_usuario_desde_request(request)
    return respuesta_exito('Lista de citas')


# ============================================
# EJEMPLO 5: Endpoint público (invitados permitidos)
# ============================================
@permite_invitado
def catalogo_servicios(request):
    """Cualquiera puede ver el catálogo, pero usuarios autenticados tienen más info"""
    usuario = obtener_usuario_desde_request(request)  # Puede ser None
    
    if usuario:
        # Usuario autenticado: mostrar información adicional
        return respuesta_exito('Catálogo completo')
    else:
        # Invitado: mostrar información básica
        return respuesta_exito('Catálogo básico')


# ============================================
# EJEMPLO 6: Endpoint solo para administrador
# ============================================
@requiere_administrador
def gestionar_empleados(request):
    """Solo administradores pueden gestionar empleados"""
    usuario = obtener_usuario_desde_request(request)
    return respuesta_exito('Gestión de empleados')


# ============================================
# EJEMPLO 7: Endpoint para staff (secretaria, barbero, admin)
# ============================================
@requiere_staff
def dashboard_staff(request):
    """Cualquier miembro del staff puede acceder"""
    usuario = obtener_usuario_desde_request(request)
    return respuesta_exito('Dashboard staff', {'rol': usuario.rol})


# ============================================
# EJEMPLO 8: Combinación de decoradores
# ============================================
# Nota: Los decoradores se aplican de abajo hacia arriba
@requiere_autenticacion  # Primero verifica autenticación
@requiere_secretaria     # Luego verifica rol
def validar_pago(request):
    """Solo secretarias autenticadas"""
    usuario = obtener_usuario_desde_request(request)
    return respuesta_exito('Validación de pago')
