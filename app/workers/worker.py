import asyncio
import aio_pika
import os
import json

from app.workers.tasks import process_type1, process_type2, process_type3
from app.dependencies import get_db
from app import crud, schemas
from app.models import TaskStatus


RABBITMQ_URL = os.getenv("RABBITMQ_URL")
QUEUE_NAME = "task_queue"


async def process_task(task_data):
    """
    Обрабатывает задачу, полученную из очереди.

    1. Загружает данные задачи из JSON.
    2. Получает задачу из базы данных.
    3. Обновляет её статус на IN_PROGRESS.
    4. Выполняет соответствующую обработку в зависимости от типа задачи.
    5. Записывает результат и обновляет статус на COMPLETED или FAILED.

    :param task_data: Данные задачи в формате JSON (байтовая строка).
    """
    task = json.loads(task_data)
    task_id = task.get('id')
    task_type = task.get('type')
    task_payload = task.get('data')

    # Получаем сессию БД
    async with get_db() as db:
        db_task = await crud.get_task(db, task_id=task_id)
        if db_task is None:
            return

        # Обновляем статус задачи на IN_PROGRESS
        await crud.update_task(
            db,
            db_task=db_task,
            updates=schemas.TaskUpdate(status=TaskStatus.IN_PROGRESS)
        )

        try:
            if task_type == 'type1':
                result = await process_type1(task_payload)
            elif task_type == 'type2':
                result = await process_type2(task_payload)
            elif task_type == 'type3':
                result = await process_type3(task_payload)
            else:
                raise ValueError(f"Unknown task type: {task_type}")

            # Сохраняем результат и обновляем статус на COMPLETED
            await crud.update_task(
                db,
                db_task=db_task,
                updates=schemas.TaskUpdate(
                    status=TaskStatus.COMPLETED,
                    result=str(result)
                )
            )

        except Exception as e:
            # В случае ошибки обновляем статус на FAILED
            await crud.update_task(
                db,
                db_task=db_task,
                updates=schemas.TaskUpdate(
                    status=TaskStatus.FAILED,
                    result=str(e)
                )
            )


async def consume():
    """
    Подключается к RabbitMQ, слушает очередь задач и обрабатывает их.

    1. Устанавливает соединение с RabbitMQ.
    2. Ожидает сообщения в очереди `task_queue`.
    3. При получении сообщения вызывает `process_task`, передавая данные задачи.
    """
    connection = await aio_pika.connect_robust(RABBITMQ_URL)
    async with connection:
        channel = await connection.channel()
        queue = await channel.declare_queue(QUEUE_NAME, durable=True)

        async with queue.iterator() as queue_iter:
            async for message in queue_iter:
                async with message.process():
                    task_data = message.body
                    await process_task(task_data)

if __name__ == "__main__":
    asyncio.run(consume())
