from rabbitmq_connection import RabbitMQConnection
import json
from datetime import datetime

def producer_example():
    """
    Ejemplo básico de producer
    Envía mensajes a la cola 'citas'
    """
    rabbitmq = RabbitMQConnection(queue_name='citas')
    rabbitmq.connect()
    
    # Mensajes de ejemplo
    messages = [
        {
            'id_cita': 1,
            'paciente': 'Juan Pérez',
            'medico': 'Dr. García',
            'fecha': '2026-04-25',
            'hora': '10:00',
            'tipo': 'Consulta General',
            'timestamp': datetime.now().isoformat()
        },
        {
            'id_cita': 2,
            'paciente': 'María López',
            'medico': 'Dra. Martínez',
            'fecha': '2026-04-25',
            'hora': '14:30',
            'tipo': 'Seguimiento',
            'timestamp': datetime.now().isoformat()
        },
        {
            'id_cita': 3,
            'paciente': 'Carlos Ruiz',
            'medico': 'Dr. Rodríguez',
            'fecha': '2026-04-26',
            'hora': '09:00',
            'tipo': 'Consulta General',
            'timestamp': datetime.now().isoformat()
        }
    ]
    
    # Envía cada mensaje
    for message in messages:
        success = rabbitmq.send_message(message)
        if success:
            print(f"✅ Cita creada: {message['paciente']} con {message['medico']}")
    
    rabbitmq.close()

if __name__ == '__main__':
    print("=" * 60)
    print("PRODUCER - Sistema de Citas")
    print("=" * 60)
    producer_example()
    print("=" * 60)
    print("✅ Todos los mensajes fueron enviados a la cola")
    print("=" * 60)
