#!/bin/bash
# Script para verificar headers de seguridad
# Uso: ./scripts/verificar_seguridad.sh

URL="https://backendbina-1.onrender.com"

echo "=========================================="
echo "VERIFICACIÓN DE HEADERS DE SEGURIDAD"
echo "=========================================="
echo ""
echo "URL: $URL"
echo ""

echo "Headers de seguridad encontrados:"
echo "----------------------------------------"
curl -I "$URL/api/usuarios/csrf/" 2>/dev/null | grep -iE "(strict-transport|frame-options|content-type|xss|content-security)"

echo ""
echo "Verificación completa en:"
echo "https://securityheaders.com/?q=$URL"
echo ""



