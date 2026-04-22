from fastapi import FastAPI, HTTPException, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional
from datetime import datetime
from rabbitmq_connection import RabbitMQConnection
from redis_lock import redis_lock
import json

# Inicializa FastAPI
app = FastAPI(
    title="Sistema de Citas Distribuido",
    description="API con colas (RabbitMQ) y coordinación (Redis)",
    version="1.0"
)

# Inicializa RabbitMQ
rabbitmq = RabbitMQConnection(queue_name='citas')

# Modelos Pydantic
class Cita(BaseModel):
    paciente: str
    medico: str
    fecha: str
    hora: str
    tipo: str

class CitaResponse(BaseModel):
    id: int
    status: str
    mensaje: str
    timestamp: str

# Base de datos simulada (en memoria)
citas_db = []
contador_citas = 0

@app.on_event("startup")
async def startup():
    """Se ejecuta al iniciar la aplicación"""
    print("🚀 Iniciando aplicación...")
    try:
        rabbitmq_check = RabbitMQConnection(queue_name='citas')
        rabbitmq_check.connect()
        rabbitmq_check.close()
        print("✅ RabbitMQ disponible")
    except Exception as e:
        print(f"⚠️  Advertencia: {e}")

@app.on_event("shutdown")
async def shutdown():
    """Se ejecuta al cerrar la aplicación"""
    print("🔌 Cerrando aplicación...")
    rabbitmq.close()

@app.get("/", tags=["Info"])
async def root():
    """Endpoint raíz con información del sistema"""
    return {
        "servicio": "Sistema de Citas Distribuido",
        "version": "1.0",
        "componentes": ["FastAPI", "RabbitMQ", "Redis"],
        "endpoints": [
            "GET /",
            "GET /health",
            "GET /citas",
            "POST /citas",
            "GET /citas/{id}",
            "DELETE /citas/{id}"
        ]
    }

@app.get("/health", tags=["Health"])
async def health():
    """Verifica el estado de la aplicación"""
    try:
        # Verifica Redis
        redis_lock.redis_client.ping()
        redis_ok = True
    except:
        redis_ok = False

    rabbitmq_check = RabbitMQConnection(queue_name='citas')
    try:
        rabbitmq_check.connect()
        rabbitmq_ok = True
    except:
        rabbitmq_ok = False
    finally:
        rabbitmq_check.close()

    return {
        "status": "healthy" if redis_ok and rabbitmq_ok else "degraded",
        "redis": "✅" if redis_ok else "❌",
        "rabbitmq": "✅" if rabbitmq_ok else "❌",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/citas", tags=["Citas"])
async def obtener_citas():
    """Obtiene todas las citas registradas"""
    return {
        "total": len(citas_db),
        "citas": citas_db
    }

@app.get("/citas/{cita_id}", tags=["Citas"])
async def obtener_cita(cita_id: int):
    """Obtiene una cita específica"""
    cita = next((c for c in citas_db if c['id'] == cita_id), None)
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    return cita

@app.post("/citas", tags=["Citas"], response_model=CitaResponse)
async def crear_cita(cita: Cita):
    """
    Crea una nueva cita y la envía a la cola
    
    Flujo:
    1. Valida datos con Pydantic
    2. Intenta adquirir lock en Redis
    3. Envía a la cola RabbitMQ
    4. Guarda en BD local
    """
    
    global contador_citas
    contador_citas += 1
    cita_id = contador_citas
    
    try:
        # PASO 1: Valida datos (Pydantic lo hace automáticamente)
        print(f"\n📋 Nueva solicitud de cita #{cita_id}")
        print(f"   Paciente: {cita.paciente}")
        print(f"   Médico: {cita.medico}")
        
        # PASO 2: Intenta adquirir lock en Redis
        print(f"   Verificando acceso (Redis)...")
        lock_key = f"cita_creation:{cita_id}"
        
        if not redis_lock.acquire_lock(lock_key, timeout=5):
            print(f"   ❌ No se puede crear cita (bloqueada)")
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Cita bloqueada por coordinación distribuida"
            )
        
        print(f"   ✅ Lock adquirido")
        
        try:
            # PASO 3: Prepara mensaje para RabbitMQ
            mensaje_cita = {
                "id_cita": cita_id,
                "paciente": cita.paciente,
                "medico": cita.medico,
                "fecha": cita.fecha,
                "hora": cita.hora,
                "tipo": cita.tipo,
                "timestamp": datetime.now().isoformat()
            }
            
            # PASO 4: Envía a la cola
            print(f"   Enviando a cola RabbitMQ...")
            if not rabbitmq.send_message(mensaje_cita):
                raise HTTPException(
                    status_code=500,
                    detail="Error enviando a la cola"
                )
            
            # PASO 5: Guarda en BD local
            cita_dict = {
                "id": cita_id,
                **mensaje_cita,
                "estado": "pendiente"
            }
            citas_db.append(cita_dict)
            
            # PASO 6: Guarda estado en Redis
            redis_lock.set_state(f"cita:{cita_id}", cita_dict)
            
            print(f"   ✅ Cita creada exitosamente")
            
            return CitaResponse(
                id=cita_id,
                status="pendiente",
                mensaje=f"Cita creada y enviada a procesamiento. ID: {cita_id}",
                timestamp=datetime.now().isoformat()
            )
        
        finally:
            # Siempre libera el lock
            redis_lock.release_lock(lock_key)
            print(f"   Lock liberado\n")
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"   ❌ Error: {e}\n")
        raise HTTPException(
            status_code=500,
            detail=f"Error creando cita: {str(e)}"
        )

@app.delete("/citas/{cita_id}", tags=["Citas"])
async def eliminar_cita(cita_id: int):
    """Elimina una cita"""
    global citas_db
    cita = next((c for c in citas_db if c['id'] == cita_id), None)
    if not cita:
        raise HTTPException(status_code=404, detail="Cita no encontrada")
    
    citas_db = [c for c in citas_db if c['id'] != cita_id]
    return {"mensaje": f"Cita {cita_id} eliminada"}

@app.get("/stats", tags=["Estadísticas"])
async def obtener_estadisticas():
    """Obtiene estadísticas del sistema"""
    return {
        "total_citas": len(citas_db),
        "citas_pendientes": len([c for c in citas_db if c.get('estado') == 'pendiente']),
        "citas_procesadas": len([c for c in citas_db if c.get('estado') == 'procesada']),
        "timestamp": datetime.now().isoformat()
    }

if __name__ == '__main__':
    import uvicorn
    print("=" * 70)
    print("🚀 INICIANDO API FastAPI")
    print("=" * 70)
    print("\n📍 URL: http://localhost:8001")
    print("📚 Docs: http://localhost:8001/docs")
    print("\n")
    uvicorn.run(app, host='0.0.0.0', port=8001)
