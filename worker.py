from rabbitmq_connection import RabbitMQConnection
from redis_lock import redis_lock
import json
from datetime import datetime
import time

# Base de datos simulada
citas_procesadas = []

def guardar_cita(cita_data: dict) -> bool:
    """
    Guarda la cita en la base de datos
    (Aquí iría la lógica de BD real)
    """
    try:
        # Simula guardado en BD
        cita_con_timestamp = {
            **cita_data,
            'estado': 'procesada',
            'procesada_en': datetime.now().isoformat()
        }
        citas_procesadas.append(cita_con_timestamp)
        
        # Guarda en Redis como respaldo
        redis_lock.set_state(f"cita:{cita_data.get('id_cita')}", cita_con_timestamp)
        
        return True
    except Exception as e:
        print(f"❌ Error guardando cita: {e}")
        return False

def enviar_notificacion(cita_data: dict) -> bool:
    """
    Envía notificación (email, SMS, etc)
    """
    try:
        print(f"   📧 Enviando notificación a {cita_data.get('paciente')}...")
        # Simula envío de notificación
        time.sleep(0.5)
        print(f"   ✅ Notificación enviada")
        return True
    except Exception as e:
        print(f"   ❌ Error enviando notificación: {e}")
        return False

def procesar_cita(ch, method, properties, body):
    """
    Callback que procesa cada cita
    """
    try:
        # Decodifica el mensaje
        cita = json.loads(body)
        cita_id = cita.get('id_cita')
        paciente = cita.get('paciente')
        
        print("\n" + "=" * 70)
        print(f"⚙️  PROCESANDO CITA #{cita_id} - {paciente}")
        print("=" * 70)
        
        # PASO 1: Intenta adquirir lock en Redis
        print(f"1. Verificando acceso (Redis Lock)...")
        if redis_lock.acquire_lock(f"cita:{cita_id}"):
            print(f"   ✅ Lock adquirido")
            
            try:
                # PASO 2: Valida la cita
                print(f"2. Validando datos de cita...")
                if not cita.get('paciente') or not cita.get('medico'):
                    raise ValueError("Faltan datos obligatorios")
                print(f"   ✅ Cita válida")
                
                # PASO 3: Guarda en BD
                print(f"3. Guardando en base de datos...")
                if guardar_cita(cita):
                    print(f"   ✅ Cita guardada")
                else:
                    raise Exception("Error al guardar cita")
                
                # PASO 4: Envía notificación
                print(f"4. Notificando al paciente...")
                enviar_notificacion(cita)
                
                # PASO 5: Libera lock
                print(f"5. Liberando lock...")
                redis_lock.release_lock(f"cita:{cita_id}")
                print(f"   ✅ Lock liberado")
                
                print("=" * 70)
                print(f"✅ CITA #{cita_id} PROCESADA EXITOSAMENTE")
                print("=" * 70)
                
            except Exception as e:
                print(f"   ❌ Error: {e}")
                redis_lock.release_lock(f"cita:{cita_id}")
                print("=" * 70)
                print(f"❌ ERROR EN CITA #{cita_id}")
                print("=" * 70)
        else:
            print(f"   ⚠️  CITA BLOQUEADA - Reintentando después...")
            # Rechaza el mensaje para reintentarlo
            ch.basic_nack(delivery_tag=method.delivery_tag)
            
    except json.JSONDecodeError:
        print(f"❌ Error decodificando mensaje")
    except Exception as e:
        print(f"❌ Error procesando cita: {e}")

def worker_main():
    """
    Inicia el worker que procesa las citas
    """
    rabbitmq = RabbitMQConnection(queue_name='citas')
    rabbitmq.connect()
    
    # Configura QoS (procesa un mensaje a la vez)
    rabbitmq.channel.basic_qos(prefetch_count=1)
    
    print("\n" + "=" * 70)
    print("🚀 WORKER INICIADO - Procesando citas")
    print("=" * 70)
    print("Esperando citas en la cola...")
    print("Presiona Ctrl+C para detener\n")
    
    try:
        rabbitmq.consume_messages(procesar_cita)
    except KeyboardInterrupt:
        print("\n\n" + "=" * 70)
        print("❌ WORKER DETENIDO")
        print("=" * 70)
        print(f"\n📊 ESTADÍSTICAS:")
        print(f"   Total citas procesadas: {len(citas_procesadas)}")
        if citas_procesadas:
            print(f"   Última cita: {citas_procesadas[-1]['paciente']}")
        rabbitmq.close()

if __name__ == '__main__':
    worker_main()
