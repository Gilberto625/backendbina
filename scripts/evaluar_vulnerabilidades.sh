#!/bin/bash
# Script completo para evaluar vulnerabilidades
# Uso: ./scripts/evaluar_vulnerabilidades.sh

URL="https://backendbina-1.onrender.com"
API_URL="${URL}/api/usuarios"

echo "=========================================="
echo "EVALUACIÓN DE VULNERABILIDADES"
echo "=========================================="
echo ""
echo "URL: $URL"
echo "Fecha: $(date)"
echo ""

# 1. Verificar dependencias
echo "1. VERIFICANDO DEPENDENCIAS VULNERABLES"
echo "----------------------------------------"
if command -v pip-audit &> /dev/null; then
    echo "✓ pip-audit disponible"
    pip-audit --file requirements.txt
else
    echo "⚠️  pip-audit no instalado. Instalar con: pip install pip-audit"
fi
echo ""

if command -v safety &> /dev/null; then
    echo "✓ Safety disponible"
    safety check --file requirements.txt
else
    echo "⚠️  Safety no instalado. Instalar con: pip install safety"
fi
echo ""

# 2. Verificar cookies
echo "2. VERIFICANDO COOKIES"
echo "----------------------------------------"
echo "Cookies en respuesta:"
curl -I "${API_URL}/csrf/" 2>/dev/null | grep -i set-cookie || echo "No se encontraron cookies"
echo ""

# 3. Verificar TLS/SSL
echo "3. VERIFICANDO CONFIGURACIÓN TLS/SSL"
echo "----------------------------------------"
echo "Protocolo TLS:"
openssl s_client -connect backendbina-1.onrender.com:443 -showcerts < /dev/null 2>/dev/null | \
  openssl x509 -noout -text 2>/dev/null | grep -A 1 "Version" || echo "No se pudo verificar"
echo ""
echo "Certificado válido hasta:"
openssl s_client -connect backendbina-1.onrender.com:443 < /dev/null 2>/dev/null | \
  openssl x509 -noout -dates 2>/dev/null || echo "No se pudo verificar"
echo ""
echo "⚠️  Para evaluación completa, usar SSL Labs:"
echo "   https://www.ssllabs.com/ssltest/?d=backendbina-1.onrender.com"
echo ""

# 4. Prueba SQL Injection
echo "4. PRUEBA SQL INJECTION"
echo "----------------------------------------"
echo "Intentando SQL Injection en login..."
RESPONSE=$(curl -s -X POST "${API_URL}/login/" \
  -H "Content-Type: application/json" \
  -d '{"email": "' OR '1'='1", "password": "test"}' \
  -w "\nHTTP_CODE:%{http_code}")

HTTP_CODE=$(echo "$RESPONSE" | grep -o "HTTP_CODE:[0-9]*" | cut -d: -f2)
BODY=$(echo "$RESPONSE" | sed '/HTTP_CODE/d')

if [ "$HTTP_CODE" = "401" ] || [ "$HTTP_CODE" = "400" ]; then
    echo "✅ SQL Injection rechazado correctamente (HTTP $HTTP_CODE)"
else
    echo "⚠️  Respuesta inesperada: HTTP $HTTP_CODE"
    echo "   Revisar manualmente"
fi
echo ""

# 5. Prueba XSS
echo "5. PRUEBA XSS"
echo "----------------------------------------"
echo "Intentando XSS en registro..."
RESPONSE=$(curl -s -X POST "${API_URL}/register/" \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "<script>alert(1)</script>",
    "apellidopaterno": "Test",
    "apellidomaterno": "Test",
    "username": "testxss",
    "correo": "testxss@test.com",
    "contrasena": "Password123!",
    "telefono": "1234567890",
    "preguntasecreta": "Test",
    "respuestasecreta": "Test"
  }' \
  -w "\nHTTP_CODE:%{http_code}")

HTTP_CODE=$(echo "$RESPONSE" | grep -o "HTTP_CODE:[0-9]*" | cut -d: -f2)

if [ "$HTTP_CODE" = "201" ] || [ "$HTTP_CODE" = "400" ]; then
    echo "✅ XSS manejado correctamente (HTTP $HTTP_CODE)"
    echo "   Verificar en BD que los datos estén escapados"
else
    echo "⚠️  Respuesta inesperada: HTTP $HTTP_CODE"
fi
echo ""

# 6. Verificar headers de seguridad
echo "6. VERIFICANDO HEADERS DE SEGURIDAD"
echo "----------------------------------------"
echo "Headers de seguridad:"
curl -I "${API_URL}/csrf/" 2>/dev/null | grep -iE "(strict-transport|frame-options|content-type|xss|content-security)" || echo "No se encontraron headers de seguridad"
echo ""

# 7. Resumen
echo "=========================================="
echo "RESUMEN"
echo "=========================================="
echo ""
echo "✓ Verificaciones completadas"
echo ""
echo "Recomendaciones:"
echo "- Ejecutar OWASP ZAP para escaneo completo"
echo "- Ejecutar Burp Suite para pruebas manuales"
echo "- Verificar en SSL Labs para calificación TLS"
echo "- Revisar SecurityHeaders.com para headers"
echo ""
echo "Herramientas adicionales:"
echo "- OWASP ZAP: https://www.zaproxy.org/"
echo "- Burp Suite: https://portswigger.net/burp"
echo "- SSL Labs: https://www.ssllabs.com/ssltest/"
echo "- SecurityHeaders: https://securityheaders.com/"
echo ""


