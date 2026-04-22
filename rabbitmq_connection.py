import pika
import json
from typing import Callable

class RabbitMQConnection:
    def __init__(self, host='localhost', queue_name='citas', durable=False):
        """Inicializa la conexión con RabbitMQ"""
        self.host = host
        self.queue_name = queue_name
        self.connection = None
        self.channel = None
        self.durable = durable

    def _is_connection_ready(self) -> bool:
        return bool(
            self.connection
            and self.channel
            and self.connection.is_open
            and self.channel.is_open
        )

    def connect(self):
        """Establece conexión con RabbitMQ"""
        if self._is_connection_ready():
            return

        try:
            self.close()
            credentials = pika.PlainCredentials('guest', 'guest')
            parameters = pika.ConnectionParameters(
                host=self.host,
                credentials=credentials
            )
            self.connection = pika.BlockingConnection(parameters)
            self.channel = self.connection.channel()

            # Declara la cola (crea si no existe)
            self.channel.queue_declare(queue=self.queue_name, durable=self.durable)
            print(f"✅ Conectado a RabbitMQ - Cola: {self.queue_name} (durable={self.durable})")
        except Exception as e:
            self.connection = None
            self.channel = None
            print(f"❌ Error conectando a RabbitMQ: {e}")
            raise

    def send_message(self, message: dict) -> bool:
        """Envía un mensaje a la cola"""
        try:
            self.connect()

            message_json = json.dumps(message)
            properties = None
            if self.durable:
                properties = pika.BasicProperties(
                    delivery_mode=pika.spec.PERSISTENT_DELIVERY_MODE
                )

            self.channel.basic_publish(
                exchange='',
                routing_key=self.queue_name,
                body=message_json,
                properties=properties
            )
            print(f"📤 Mensaje enviado a la cola: {message}")
            return True
        except Exception as e:
            print(f"❌ Error enviando mensaje: {e}")
            self.close()
            return False

    def consume_messages(self, callback: Callable):
        """Consume mensajes de la cola"""
        try:
            self.connect()

            # Configura el callback
            self.channel.basic_consume(
                queue=self.queue_name,
                on_message_callback=callback,
                auto_ack=True
            )

            print(f"👂 Escuchando mensajes en la cola: {self.queue_name}")
            self.channel.start_consuming()
        except Exception as e:
            print(f"❌ Error consumiendo mensajes: {e}")
            self.close()

    def close(self):
        """Cierra la conexión"""
        try:
            if self.channel and self.channel.is_open:
                self.channel.close()
            if self.connection and not self.connection.is_closed:
                self.connection.close()
                print("🔌 Conexión cerrada")
        finally:
            self.channel = None
            self.connection = None
