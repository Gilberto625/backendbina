# 📋 Instrucciones para Aplicar Mejoras de Seguridad

## ⚠️ IMPORTANTE: Ejecutar Migración

Se han agregado nuevos campos al modelo `Usuario` para protección contra fuerza bruta. **Debes ejecutar la migración antes de desplegar**.

### Pasos:

1. **Activar entorno virtual** (si usas uno):
```bash
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

2. **Crear migración**:
```bash
cd backendbina
python manage.py makemigrations accounts
```

3. **Aplicar migración**:
```bash
python manage.py migrate
```

### Campos Agregados:
- `intentos_fallidos` (IntegerField, default=0)
- `bloqueado_hasta` (DateTimeField, null=True, blank=True)
- `ultimo_intento` (DateTimeField, null=True, blank=True)

---

## ✅ Resumen de Mejoras Implementadas

### 1. Bloqueo por Intentos Fallidos ✅
- Bloquea cuenta después de 3 intentos fallidos
- Bloqueo temporal de 15 minutos
- Mensajes informativos de intentos restantes

### 2. Sesiones Expiradas ✅
- Sesiones expiran después de 15 minutos de inactividad
- Configurado en `settings.py`: `SESSION_COOKIE_AGE = 900`

### 3. Revocación de Sesiones ✅
- Endpoint `POST /api/usuarios/logout/` implementado
- Endpoint `GET /api/usuarios/verificar-sesion/` implementado

### 4. MFA/TOTP ✅
- Requiere segundo factor si `totp_enabled=True`
- Envía código OTP por email cuando MFA está habilitado

### 5. OAuth2.0 Seguro ✅
- Google login verificado con Firebase Admin SDK
- Tokens no expuestos en URLs ni logs

### 6. Pregunta Secreta Segura ✅
- Valida respuestas comunes y débiles
- Rechaza respuestas como "123", "password", "admin", etc.

### 7. HTTPS ✅
- Configurado para producción
- Cookies seguras habilitadas

---

## 📝 Archivos Modificados

1. `accounts/models.py` - Campos de bloqueo agregados
2. `accounts/utils/security_utils.py` - **NUEVO** - Utilidades de seguridad
3. `accounts/views.py` - Bloqueo, logout, verificación de sesión, MFA
4. `accounts/urls.py` - Nuevas rutas agregadas
5. `core/settings.py` - Configuración de sesiones actualizada

---

## 🧪 Pruebas Post-Despliegue

Después de aplicar la migración y desplegar:

1. **Bloqueo por intentos fallidos**:
   - Intentar login 3 veces con contraseña incorrecta
   - Verificar que la cuenta se bloquee por 15 minutos

2. **Sesiones expiradas**:
   - Iniciar sesión
   - Esperar 15 minutos sin actividad
   - Verificar que la sesión expire

3. **Logout**:
   - Iniciar sesión
   - Cerrar sesión con `POST /api/usuarios/logout/`
   - Verificar que la sesión se invalide

4. **MFA**:
   - Activar TOTP para un usuario
   - Intentar login
   - Verificar que se requiera segundo factor

5. **Pregunta secreta**:
   - Intentar registro con respuesta común ("123")
   - Verificar que sea rechazada

---

## ✅ Estado

**Todas las mejoras están implementadas y listas para desplegar.**

Solo falta ejecutar la migración antes del despliegue.

