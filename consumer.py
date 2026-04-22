from rabbitmq_connection import RabbitMQConnection
import json
from datetime import datetime

def process_message(ch, method, properties, body):
    """
    Callback que procesa cada mensaje recibido
    """
    try:
        # Decodifica el mensaje
        message = json.loads(body)
        
        print("\n" + "=" * 60)
        print("📨 NUEVO MENSAJE RECIBIDO")
        print("=" * 60)
        print(f"ID Cita: {message.get('id_cita')}")
        print(f"Paciente: {message.get('paciente')}")
        print(f"Médico: {message.get('medico')}")
        print(f"Fecha: {message.get('fecha')}")
        print(f"Hora: {message.get('hora')}")
        print(f"Tipo: {message.get('tipo')}")
        print(f"Recibido: {datetime.now().isoformat()}")
        print("=" * 60)
        
        # Aquí va la lógica de procesamiento
        # Por ejemplo: guardar en BD, enviar notificación, etc.
        
    except json.JSONDecodeError:
        print(f"❌ Error decodificando mensaje: {body}")
    except Exception as e:
        print(f"❌ Error procesando mensaje: {e}")

def consumer_example():
    """
    Ejemplo de consumer
    Escucha la cola 'citas' y procesa los mensajes
    """
    rabbitmq = RabbitMQConnection(queue_name='citas')
    rabbitmq.connect()
    
    print("\n👂 Escuchando mensajes...")
    print("Presiona Ctrl+C para detener\n")
    
    try:
        rabbitmq.consume_messages(process_message)
    except KeyboardInterrupt:
        print("\n\n❌ Consumer detenido")
        rabbitmq.close()

if __name__ == '__main__':
    print("=" * 60)
    print("CONSUMER - Sistema de Citas")
    print("=" * 60)
    consumer_example()
