# Integración Bancaria - Pendiente

## 📋 Estado Actual

**Estado**: ⏳ **PENDIENTE - Banco no definido**

El dueño del negocio aún no ha definido qué banco utilizará para recibir el dinero de las compras de los clientes.

## ✅ Lo que ya está implementado

1. **Validación manual de transferencias**
   - La secretaria puede validar transferencias manualmente
   - Se almacena el ID de operación bancaria
   - Se actualiza el estado del pago automáticamente

2. **Estructura base**
   - Modelo `Pago` con campo `id_operacion` para almacenar ID de transferencia
   - Endpoint `/api/pagos/{id}/validar-transferencia/` para validación manual
   - Servicio `PagosService.validar_transferencia_bancaria()` listo para extender

3. **Flujo de trabajo actual**
   - Cliente crea pago con método "transferencia" y proporciona ID de operación
   - Pago queda en estado "procesando"
   - Secretaria valida manualmente el pago
   - Sistema actualiza estado a "completado" y procesa cita/compra asociada

## 🔧 Lo que falta implementar (una vez definido el banco)

### Opción 1: Banco con API disponible

Si el banco proporciona una API para verificar transferencias:

1. **Obtener credenciales del banco**
   - API Key / Access Token
   - Endpoint de verificación
   - Documentación de la API

2. **Instalar SDK del banco** (si existe)
   ```bash
   pip install nombre-sdk-banco
   ```

3. **Modificar `pagos/services.py`**
   - Actualizar función `validar_transferencia_bancaria()`
   - Agregar llamada a API del banco para verificar transferencia
   - Manejar respuestas de la API

4. **Configurar variables de entorno**
   ```bash
   BANCO_API_KEY=tu_api_key
   BANCO_API_URL=https://api.banco.com
   ```

5. **Implementar verificación automática** (opcional)
   - Endpoint para verificar transferencias automáticamente
   - Tarea periódica (Celery) para verificar pagos pendientes

### Opción 2: Banco con Webhook

Si el banco envía notificaciones (webhooks) cuando se recibe una transferencia:

1. **Configurar webhook en el banco**
   - URL del webhook: `https://tudominio.com/api/pagos/webhook/banco/`
   - Configurar eventos a recibir

2. **Crear endpoint de webhook**
   - `POST /api/pagos/webhook/banco/`
   - Validar firma del webhook (si aplica)
   - Procesar notificación
   - Actualizar estado del pago

3. **Modificar `pagos/services.py`**
   - Agregar función `procesar_webhook_banco()`
   - Mapear datos del webhook al modelo `Pago`

### Opción 3: Banco sin API (solo validación manual)

Si el banco no proporciona API ni webhooks:

1. **Mantener validación manual actual**
   - El sistema actual ya soporta esto
   - Solo mejorar la interfaz de validación

2. **Mejorar proceso de validación** (opcional)
   - Agregar más campos de validación (fecha, monto, etc.)
   - Agregar notas/comentarios en la validación
   - Historial de validaciones

## 📝 Archivos a modificar cuando se defina el banco

### 1. `pagos/services.py`
```python
def validar_transferencia_bancaria(pago, id_operacion, validado_por):
    """
    Valida un pago por transferencia bancaria
    
    TODO: Implementar integración con API del banco cuando se defina
    """
    # Aquí se agregará la llamada a la API del banco
    pass
```

### 2. `pagos/views.py`
```python
@csrf_exempt
@requiere_secretaria
def validar_transferencia(request, pago_id):
    """
    Valida un pago por transferencia bancaria
    
    TODO: Agregar verificación automática con banco cuando se defina
    """
    # Aquí se agregará la verificación automática
    pass
```

### 3. `core/settings.py`
```python
# Agregar configuración del banco
BANCO_API_KEY = config('BANCO_API_KEY', default='')
BANCO_API_URL = config('BANCO_API_URL', default='')
```

### 4. `pagos/urls.py` (si hay webhook)
```python
path('webhook/banco/', views.webhook_banco, name='webhook_banco'),
```

## 🔍 Información necesaria del banco

Cuando se defina el banco, se necesita:

- [ ] Nombre del banco
- [ ] ¿Tiene API disponible?
- [ ] ¿Tiene webhooks?
- [ ] Credenciales de acceso (API Key, Token, etc.)
- [ ] Documentación de la API
- [ ] Endpoints disponibles
- [ ] Formato de IDs de operación
- [ ] Métodos de autenticación
- [ ] Límites de rate limiting
- [ ] Ambiente de pruebas (sandbox)

## 📞 Contacto

Una vez que se defina el banco, contactar al equipo de desarrollo para implementar la integración.

---

*Documento creado - 28 de enero de 2026*
*Actualizar cuando se defina el banco*
