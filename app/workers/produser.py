import aio_pika
import os
import json

RABBITMQ_URL = os.getenv("RABBITMQ_URL")
QUEUE_NAME = "task_queue"


async def send_task_to_queue(task):
    """
    Отправляет задачу в очередь RabbitMQ.

    :param task: Словарь с данными задачи, который будет отправлен в очередь.
    """
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    async with connection:
        channel = await connection.channel()
        await channel.default_exchange.publish(
            aio_pika.Message(
                body=json.dumps(task).encode(),
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT
            ),
            routing_key=QUEUE_NAME,
        )