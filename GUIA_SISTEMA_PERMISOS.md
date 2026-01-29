# Guía del Sistema de Permisos y Decoradores

## 📋 Descripción

Sistema de permisos basado en roles para controlar el acceso a los endpoints de la API. Utiliza decoradores de Python para verificar roles de manera elegante y reutilizable.

## 🎯 Roles Disponibles

- **`cliente`**: Usuarios regulares que agendan citas y compran productos
- **`secretaria`**: Personal que gestiona citas, valida pagos y registra ventas
- **`barbero`**: Barberos que gestionan sus tiempos de servicio
- **`administrador`**: Dueño/gerente con acceso total al sistema

## 🔧 Decoradores Disponibles

### Decoradores Básicos

#### `@requiere_autenticacion`
Verifica que el usuario esté autenticado (cualquier rol).

```python
from core.decorators import requiere_autenticacion

@requiere_autenticacion
def mi_endpoint(request):
    usuario = request.usuario_autenticado
    return JsonResponse({'ok': True})
```

#### `@permite_invitado`
Permite acceso tanto a usuarios autenticados como invitados.

```python
from core.decorators import permite_invitado

@permite_invitado
def catalogo_publico(request):
    usuario = request.usuario_autenticado  # Puede ser None
    # Lógica para invitados y autenticados
    return JsonResponse({'ok': True})
```

### Decoradores por Rol

#### `@requiere_cliente`
Solo usuarios con rol `cliente`.

```python
from core.decorators import requiere_cliente

@requiere_cliente
def agendar_cita(request):
    usuario = request.usuario_autenticado
    # Solo clientes pueden agendar
    return JsonResponse({'ok': True})
```

#### `@requiere_secretaria`
Solo usuarios con rol `secretaria`.

```python
from core.decorators import requiere_secretaria

@requiere_secretaria
def validar_pago(request):
    usuario = request.usuario_autenticado
    # Solo secretarias pueden validar pagos
    return JsonResponse({'ok': True})
```

#### `@requiere_barbero`
Solo usuarios con rol `barbero`.

```python
from core.decorators import requiere_barbero

@requiere_barbero
def actualizar_tiempos(request):
    usuario = request.usuario_autenticado
    # Solo barberos pueden actualizar tiempos
    return JsonResponse({'ok': True})
```

#### `@requiere_administrador`
Solo usuarios con rol `administrador`.

```python
from core.decorators import requiere_administrador

@requiere_administrador
def gestionar_empleados(request):
    usuario = request.usuario_autenticado
    # Solo administradores pueden gestionar empleados
    return JsonResponse({'ok': True})
```

### Decoradores Compuestos

#### `@requiere_staff`
Permite acceso a secretaria, barbero o administrador.

```python
from core.decorators import requiere_staff

@requiere_staff
def dashboard_staff(request):
    usuario = request.usuario_autenticado
    # Cualquier miembro del staff puede acceder
    return JsonResponse({'ok': True})
```

#### `@requiere_admin_o_secretaria`
Permite acceso a administrador o secretaria.

```python
from core.decorators import requiere_admin_o_secretaria

@requiere_admin_o_secretaria
def gestionar_citas(request):
    usuario = request.usuario_autenticado
    # Admin o secretaria pueden gestionar citas
    return JsonResponse({'ok': True})
```

#### `@requiere_rol(*roles)`
Permite especificar múltiples roles personalizados.

```python
from core.decorators import requiere_rol

@requiere_rol('cliente', 'secretaria')
def ver_citas(request):
    usuario = request.usuario_autenticado
    # Clientes y secretarias pueden ver citas
    return JsonResponse({'ok': True})
```

## 🛠️ Utilidades

### `obtener_usuario_desde_request(request)`
Obtiene el usuario autenticado desde el request.

```python
from core.utils import obtener_usuario_desde_request

def mi_vista(request):
    usuario = obtener_usuario_desde_request(request)
    if usuario:
        return JsonResponse({'email': usuario.email})
    return JsonResponse({'error': 'No autenticado'}, status=401)
```

### `respuesta_exito(mensaje, datos=None, codigo=200)`
Crea una respuesta JSON de éxito estandarizada.

```python
from core.utils import respuesta_exito

def mi_vista(request):
    return respuesta_exito('Operación exitosa', {'id': 123})
```

### `respuesta_error(mensaje, codigo=400, detalles=None)`
Crea una respuesta JSON de error estandarizada.

```python
from core.utils import respuesta_error

def mi_vista(request):
    return respuesta_error('Error en la operación', codigo=400)
```

### `serializar_usuario(usuario, campos_adicionales=None)`
Serializa un usuario a diccionario para respuestas JSON.

```python
from core.utils import serializar_usuario

def mi_vista(request):
    usuario = obtener_usuario_desde_request(request)
    datos_usuario = serializar_usuario(usuario)
    return JsonResponse({'usuario': datos_usuario})
```

## 📝 Ejemplos de Uso Completo

### Ejemplo 1: Endpoint de Cliente

```python
from core.decorators import requiere_cliente
from core.utils import respuesta_exito, obtener_usuario_desde_request
from django.http import JsonResponse

@requiere_cliente
def mis_citas(request):
    """Lista las citas del cliente autenticado"""
    usuario = obtener_usuario_desde_request(request)
    
    # Obtener citas del cliente
    from citas.models import Cita
    citas = Cita.objects.filter(cliente=usuario)
    
    datos_citas = [{
        'id': cita.id,
        'fecha_hora': cita.fecha_hora.isoformat(),
        'servicio': cita.servicio.nombre,
        'estado': cita.estado
    } for cita in citas]
    
    return respuesta_exito('Citas obtenidas', {'citas': datos_citas})
```

### Ejemplo 2: Endpoint de Secretaria

```python
from core.decorators import requiere_secretaria
from core.utils import respuesta_exito, respuesta_error, obtener_usuario_desde_request

@requiere_secretaria
def validar_transferencia(request):
    """Valida un pago por transferencia"""
    import json
    from pagos.models import Pago
    
    try:
        data = json.loads(request.body)
        pago_id = data.get('pago_id')
        id_operacion = data.get('id_operacion')
        
        pago = Pago.objects.get(id=pago_id)
        secretaria = obtener_usuario_desde_request(request)
        
        if pago.validar_transferencia(secretaria):
            return respuesta_exito('Pago validado exitosamente')
        else:
            return respuesta_error('No se pudo validar el pago')
            
    except Pago.DoesNotExist:
        return respuesta_error('Pago no encontrado', codigo=404)
    except Exception as e:
        return respuesta_error('Error al validar pago', detalles=str(e))
```

### Ejemplo 3: Endpoint Público

```python
from core.decorators import permite_invitado
from core.utils import respuesta_exito, obtener_usuario_desde_request

@permite_invitado
def catalogo_servicios(request):
    """Muestra catálogo de servicios (público)"""
    from citas.models import Servicio
    
    servicios = Servicio.objects.filter(activo=True)
    usuario = obtener_usuario_desde_request(request)
    
    datos_servicios = [{
        'id': s.id,
        'nombre': s.nombre,
        'precio': float(s.precio_base),
        'duracion': s.duracion_minutos
    } for s in servicios]
    
    respuesta = {'servicios': datos_servicios}
    
    # Si está autenticado, agregar información adicional
    if usuario:
        respuesta['usuario_autenticado'] = True
        respuesta['rol'] = usuario.rol
    
    return respuesta_exito('Catálogo de servicios', respuesta)
```

### Ejemplo 4: Endpoint con Múltiples Roles

```python
from core.decorators import requiere_rol
from core.utils import respuesta_exito, obtener_usuario_desde_request

@requiere_rol('cliente', 'secretaria', 'administrador')
def ver_historial(request):
    """Clientes ven su historial, staff ve todos"""
    usuario = obtener_usuario_desde_request(request)
    
    from citas.models import Cita
    
    if usuario.rol == 'cliente':
        citas = Cita.objects.filter(cliente=usuario)
    else:
        # Staff puede ver todas las citas
        citas = Cita.objects.all()
    
    # Serializar y retornar
    return respuesta_exito('Historial obtenido', {'citas': [...]})
```

## ⚠️ Respuestas de Error

Los decoradores retornan automáticamente respuestas JSON con errores:

### Error 401 (No Autenticado)
```json
{
    "error": "Autenticación requerida",
    "mensaje": "Debes iniciar sesión para acceder a este recurso"
}
```

### Error 403 (Acceso Denegado)
```json
{
    "error": "Acceso denegado",
    "mensaje": "No tienes permisos para acceder a este recurso. Roles requeridos: administrador, secretaria"
}
```

## 🔄 Orden de Aplicación de Decoradores

Los decoradores se aplican de **abajo hacia arriba**:

```python
@requiere_autenticacion  # Se ejecuta primero
@requiere_secretaria     # Se ejecuta después
def mi_vista(request):
    ...
```

Es equivalente a:

```python
@requiere_rol('secretaria')
@requiere_autenticacion
def mi_vista(request):
    ...
```

## 📚 Archivos Relacionados

- `core/decorators.py`: Decoradores de permisos
- `core/utils.py`: Utilidades para vistas
- `core/middleware.py`: Middleware de autenticación
- `core/ejemplos_uso_decoradores.py`: Ejemplos de uso

## ✅ Buenas Prácticas

1. **Siempre usa decoradores** en endpoints que requieren autenticación
2. **Usa el rol más específico** posible (ej: `@requiere_secretaria` en lugar de `@requiere_staff`)
3. **Usa `obtener_usuario_desde_request()`** para obtener el usuario en las vistas
4. **Usa `respuesta_exito()` y `respuesta_error()`** para respuestas estandarizadas
5. **No confíes solo en el frontend** para validar permisos, siempre valida en el backend

---

*Sistema de permisos implementado - Fase 2 Backend*
