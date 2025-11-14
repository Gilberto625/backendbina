#!/usr/bin/env python3
"""
Script de prueba para verificar que el backend en producción funciona correctamente
"""

import requests
import json

BASE_URL = "https://backendbina-1.onrender.com/api/usuarios"
HEADERS = {
    "Content-Type": "application/json",
    "Origin": "https://frontbina.vercel.app"
}

def test_endpoint(name, method, endpoint, data=None):
    """Prueba un endpoint y muestra el resultado"""
    url = f"{BASE_URL}{endpoint}"
    print(f"\n{'='*60}")
    print(f"Probando: {name}")
    print(f"URL: {url}")
    print(f"Método: {method}")

    try:
        if method == "GET":
            response = requests.get(url, headers=HEADERS, timeout=10)
        elif method == "POST":
            print(f"Data: {json.dumps(data, indent=2)}")
            response = requests.post(url, headers=HEADERS, json=data, timeout=10)

        print(f"\nStatus Code: {response.status_code}")

        # Intentar parsear JSON
        try:
            json_response = response.json()
            print(f"Response: {json.dumps(json_response, indent=2)}")
        except:
            print(f"Response (text): {response.text[:200]}")

        # Mostrar algunos headers importantes
        print(f"\nHeaders importantes:")
        for header in ['Access-Control-Allow-Origin', 'Content-Type', 'X-Frame-Options']:
            if header in response.headers:
                print(f"  {header}: {response.headers[header]}")

        return response.status_code == 200 or response.status_code == 201

    except requests.exceptions.Timeout:
        print("❌ ERROR: Timeout - El servidor tardó demasiado en responder")
        return False
    except requests.exceptions.ConnectionError:
        print("❌ ERROR: No se pudo conectar al servidor")
        return False
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def main():
    print("="*60)
    print("PRUEBAS DE PRODUCCIÓN - Backend Bina")
    print("="*60)

    tests = [
        {
            "name": "1. CSRF Token",
            "method": "GET",
            "endpoint": "/csrf/",
            "data": None
        },
        {
            "name": "2. Estado de Seguridad (usuario inexistente)",
            "method": "POST",
            "endpoint": "/seguridad/estado/",
            "data": {"email": "noexiste@example.com"}
        },
        {
            "name": "3. Registro de Usuario (intento)",
            "method": "POST",
            "endpoint": "/register/",
            "data": {
                "nombre": "Test",
                "apellidopaterno": "User",
                "apellidomaterno": "Demo",
                "username": f"testuser_prod_{hash('test') % 10000}",
                "correo": "test_production@example.com",
                "contrasena": "TestPassword123!",
                "telefono": "5551234567",
                "preguntasecreta": "¿Color favorito?",
                "respuestasecreta": "Azul"
            }
        }
    ]

    results = []
    for test in tests:
        success = test_endpoint(
            test["name"],
            test["method"],
            test["endpoint"],
            test["data"]
        )
        results.append((test["name"], success))

    # Resumen
    print("\n" + "="*60)
    print("RESUMEN DE PRUEBAS")
    print("="*60)
    for name, success in results:
        status = "✅ PASÓ" if success else "❌ FALLÓ"
        print(f"{status} - {name}")

    print("\n" + "="*60)
    print("DIAGNÓSTICO")
    print("="*60)

    if all(success for _, success in results):
        print("✅ Todos los tests pasaron - El backend está funcionando correctamente")
    else:
        print("⚠️ Algunos tests fallaron. Posibles causas:")
        print("  1. El deploy aún está en proceso")
        print("  2. Problema con variables de entorno")
        print("  3. Error en las migraciones de base de datos")
        print("  4. Problema con CORS")
        print("\nRecomendaciones:")
        print("  - Verifica los logs en Render Dashboard")
        print("  - Asegúrate de que RESEND_API_KEY esté configurada")
        print("  - Verifica que las migraciones se hayan ejecutado")

if __name__ == "__main__":
    main()
