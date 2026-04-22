#!/usr/bin/env python3
"""
Script de prueba automatizado para el sistema distribuido de citas
Verifica que todos los componentes funcionen correctamente
"""

import requests
import json
import time
from datetime import datetime

# Configuración
API_URL = "http://localhost:8001"
TIMEOUT = 5

class Colors:
    """Colores para terminal"""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'

def print_success(msg):
    print(f"{Colors.GREEN}✅ {msg}{Colors.END}")

def print_error(msg):
    print(f"{Colors.RED}❌ {msg}{Colors.END}")

def print_info(msg):
    print(f"{Colors.BLUE}ℹ️  {msg}{Colors.END}")

def print_warning(msg):
    print(f"{Colors.YELLOW}⚠️  {msg}{Colors.END}")

def test_health():
    """Prueba 1: Verificar salud del sistema"""
    print("\n" + "="*60)
    print("PRUEBA 1: Health Check")
    print("="*60)
    
    try:
        response = requests.get(f"{API_URL}/health", timeout=TIMEOUT)
        data = response.json()
        
        if response.status_code == 200:
            print_success("API respondiendo")
            print(f"  Status: {data['status']}")
            print(f"  Redis: {data['redis']}")
            print(f"  RabbitMQ: {data['rabbitmq']}")
            return True
        else:
            print_error(f"API retornó {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error conectando a API: {e}")
        return False

def test_get_citas():
    """Prueba 2: Obtener citas existentes"""
    print("\n" + "="*60)
    print("PRUEBA 2: Obtener Citas")
    print("="*60)
    
    try:
        response = requests.get(f"{API_URL}/citas", timeout=TIMEOUT)
        data = response.json()
        
        if response.status_code == 200:
            print_success(f"Citas obtenidas: {data['total']} encontradas")
            for cita in data['citas'][:3]:  # Mostrar las primeras 3
                print(f"  - {cita['paciente']} ({cita['estado']})")
            return True
        else:
            print_error(f"Error: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_crear_cita():
    """Prueba 3: Crear una cita"""
    print("\n" + "="*60)
    print("PRUEBA 3: Crear Cita")
    print("="*60)
    
    try:
        # Datos de prueba
        nueva_cita = {
            "paciente": f"Paciente Test {datetime.now().timestamp()}",
            "medico": "Dr. Test",
            "fecha": "2026-05-15",
            "hora": "10:30",
            "tipo": "Consulta General"
        }
        
        print_info(f"Creando cita para {nueva_cita['paciente']}...")
        
        response = requests.post(
            f"{API_URL}/citas",
            json=nueva_cita,
            timeout=TIMEOUT
        )
        
        data = response.json()
        
        if response.status_code == 200:
            print_success(f"Cita creada: ID {data['id']}")
            print(f"  Status: {data['status']}")
            print(f"  Mensaje: {data['mensaje']}")
            return True, data['id']
        else:
            print_error(f"Error: {response.status_code}")
            print(f"  Detalles: {data}")
            return False, None
    except Exception as e:
        print_error(f"Error: {e}")
        return False, None

def test_obtener_cita_especifica(cita_id):
    """Prueba 4: Obtener una cita específica"""
    print("\n" + "="*60)
    print(f"PRUEBA 4: Obtener Cita #{cita_id}")
    print("="*60)
    
    try:
        response = requests.get(
            f"{API_URL}/citas/{cita_id}",
            timeout=TIMEOUT
        )
        
        if response.status_code == 200:
            data = response.json()
            print_success(f"Cita obtenida")
            print(f"  Paciente: {data['paciente']}")
            print(f"  Médico: {data['medico']}")
            print(f"  Fecha: {data['fecha']} a las {data['hora']}")
            print(f"  Estado: {data['estado']}")
            return True
        else:
            print_error(f"Cita no encontrada")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_estadisticas():
    """Prueba 5: Obtener estadísticas"""
    print("\n" + "="*60)
    print("PRUEBA 5: Estadísticas")
    print("="*60)
    
    try:
        response = requests.get(f"{API_URL}/stats", timeout=TIMEOUT)
        data = response.json()
        
        if response.status_code == 200:
            print_success("Estadísticas obtenidas")
            print(f"  Total citas: {data['total_citas']}")
            print(f"  Pendientes: {data['citas_pendientes']}")
            print(f"  Procesadas: {data['citas_procesadas']}")
            return True
        else:
            print_error(f"Error: {response.status_code}")
            return False
    except Exception as e:
        print_error(f"Error: {e}")
        return False

def test_multiples_citas():
    """Prueba 6: Crear múltiples citas"""
    print("\n" + "="*60)
    print("PRUEBA 6: Múltiples Citas")
    print("="*60)
    
    citas_data = [
        {
            "paciente": "María García",
            "medico": "Dra. López",
            "fecha": "2026-05-20",
            "hora": "09:00",
            "tipo": "Consulta General"
        },
        {
            "paciente": "Pedro Martínez",
            "medico": "Dr. Rodríguez",
            "fecha": "2026-05-21",
            "hora": "14:00",
            "tipo": "Seguimiento"
        },
        {
            "paciente": "Laura Sánchez",
            "medico": "Dra. Martínez",
            "fecha": "2026-05-22",
            "hora": "11:00",
            "tipo": "Revisión"
        }
    ]
    
    exitosas = 0
    for cita in citas_data:
        try:
            response = requests.post(
                f"{API_URL}/citas",
                json=cita,
                timeout=TIMEOUT
            )
            if response.status_code == 200:
                exitosas += 1
                print_success(f"Cita creada: {cita['paciente']}")
            else:
                print_error(f"Error creando cita para {cita['paciente']}")
            time.sleep(0.5)  # Pequeña pausa entre solicitudes
        except Exception as e:
            print_error(f"Error: {e}")
    
    print_info(f"Resultado: {exitosas}/{len(citas_data)} citas creadas exitosamente")
    return exitosas == len(citas_data)

def main():
    """Ejecuta todas las pruebas"""
    print("\n" + "🧪 PRUEBAS DEL SISTEMA DISTRIBUIDO")
    print("="*60)
    print(f"API URL: {API_URL}")
    print(f"Hora: {datetime.now().isoformat()}")
    print("="*60)
    
    resultados = {
        "Health Check": False,
        "Obtener Citas": False,
        "Crear Cita": False,
        "Obtener Cita Específica": False,
        "Estadísticas": False,
        "Múltiples Citas": False
    }
    
    # Prueba 1
    resultados["Health Check"] = test_health()
    
    # Prueba 2
    resultados["Obtener Citas"] = test_get_citas()
    
    # Prueba 3
    crear_ok, cita_id = test_crear_cita()
    resultados["Crear Cita"] = crear_ok
    
    # Prueba 4
    if cita_id:
        time.sleep(1)
        resultados["Obtener Cita Específica"] = test_obtener_cita_especifica(cita_id)
    
    # Prueba 5
    resultados["Estadísticas"] = test_estadisticas()
    
    # Prueba 6
    resultados["Múltiples Citas"] = test_multiples_citas()
    
    # Resumen
    print("\n" + "="*60)
    print("📊 RESUMEN DE PRUEBAS")
    print("="*60)
    
    for prueba, resultado in resultados.items():
        if resultado:
            print_success(prueba)
        else:
            print_error(prueba)
    
    total_exitosas = sum(1 for r in resultados.values() if r)
    total_pruebas = len(resultados)
    
    print("\n" + "="*60)
    if total_exitosas == total_pruebas:
        print_success(f"TODAS LAS PRUEBAS PASARON ({total_exitosas}/{total_pruebas})")
    else:
        print_warning(f"Algunas pruebas fallaron ({total_exitosas}/{total_pruebas})")
    print("="*60 + "\n")

if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Pruebas canceladas")
    except Exception as e:
        print(f"\n\n❌ Error inesperado: {e}")
