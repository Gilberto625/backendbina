# 🔍 Instrucciones para Auditoría de Seguridad

## Herramientas Requeridas

### 1. OWASP ZAP
- **Descarga**: https://www.zaproxy.org/download/
- **Instalación**: Descomprimir y ejecutar `zap.sh` o `zap.bat`

### 2. Burp Suite Community
- **Descarga**: https://portswigger.net/burp/communitydownload
- **Instalación**: Ejecutar instalador

### 3. pip-audit
```bash
pip install pip-audit
```

### 4. Safety
```bash
pip install safety
```

### 5. Snyk (Opcional)
```bash
npm install -g snyk
snyk auth
```

---

## Proceso de Auditoría

### Paso 1: Análisis de Dependencias

```bash
cd backendbina

# Con pip-audit
pip-audit

# Con Safety
safety check --file requirements.txt

# Con Snyk (si está instalado)
snyk test --file=requirements.txt
```

**Resultado esperado**: Sin vulnerabilidades críticas

---

### Paso 2: Escaneo con OWASP ZAP

1. **Iniciar ZAP**
2. **Quick Start** → **Automated Scan**
3. **URL**: `https://backendbina-1.onrender.com`
4. **Esperar** que termine el escaneo
5. **Revisar Alertas**:
   - High Risk
   - Medium Risk
   - Verificar falsos positivos

**Alertas esperadas**:
- ✅ Sin SQL Injection
- ✅ Sin XSS crítico
- ⚠️ Algunos falsos positivos pueden aparecer

---

### Paso 3: Pruebas Manuales con Burp Suite

1. **Configurar Proxy**: 127.0.0.1:8080
2. **Interceptar** requests de login/registro
3. **Modificar** parámetros con payloads SQL/XSS
4. **Verificar** respuestas

**Payloads a probar**:
```
Email: ' OR '1'='1
Nombre: <script>alert(1)</script>
```

---

### Paso 4: Verificación SSL/TLS

1. Visitar: https://www.ssllabs.com/ssltest/
2. Ingresar: `backendbina-1.onrender.com`
3. Esperar resultados
4. Verificar calificación: **A** o **A+**

---

### Paso 5: Verificación de Cookies

1. Abrir DevTools (F12)
2. Application → Cookies
3. Verificar atributos:
   - HttpOnly: ✅
   - Secure: ✅
   - SameSite: Lax ✅

---

## Scripts de Verificación

### Ejecutar Evaluación Completa

```bash
cd backendbina
chmod +x scripts/evaluar_vulnerabilidades.sh
./scripts/evaluar_vulnerabilidades.sh
```

### Verificar Cookies

```bash
python manage.py shell < scripts/verificar_cookies.py
```

---

## Reporte de Auditoría

### Template de Reporte

```markdown
# Reporte de Auditoría de Seguridad

## Fecha: [FECHA]
## Auditor: [NOMBRE]
## Sistema: Backend Bina

### 1. Dependencias
- pip-audit: [RESULTADO]
- Safety: [RESULTADO]
- Snyk: [RESULTADO]

### 2. OWASP ZAP
- Alertas High: [NÚMERO]
- Alertas Medium: [NÚMERO]
- Falsos positivos: [LISTA]

### 3. SQL Injection
- Resultado: [PASÓ/FALLÓ]
- Observaciones: [NOTAS]

### 4. XSS
- Resultado: [PASÓ/FALLÓ]
- Observaciones: [NOTAS]

### 5. SSL/TLS
- Calificación SSL Labs: [A/A+/B/etc]
- TLS versión: [1.2/1.3]

### 6. Cookies
- HttpOnly: [SÍ/NO]
- Secure: [SÍ/NO]
- SameSite: [Lax/Strict/None]

### 7. Recomendaciones
[LISTA DE RECOMENDACIONES]
```

---

## Checklist Final

- [ ] Dependencias verificadas sin CVEs críticas
- [ ] OWASP ZAP ejecutado sin vulnerabilidades críticas
- [ ] SQL Injection probado y rechazado
- [ ] XSS probado y escapado correctamente
- [ ] SSL Labs: Calificación A o superior
- [ ] Cookies con atributos correctos
- [ ] Headers de seguridad presentes
- [ ] Sesiones se invalidan correctamente

---

## Contacto

Para preguntas sobre la auditoría, consultar:
- Documentación: `EVALUACION_VULNERABILIDADES.md`
- Scripts: `scripts/evaluar_vulnerabilidades.sh`


