from sqlalchemy.orm import Session
from sqlalchemy.ext.asyncio import AsyncSession
from . import models, schemas
from datetime import datetime
from app.utils.caching import get_cache, set_cache
from typing import Optional
from sqlalchemy.future import select


async def get_tasks(
    db: AsyncSession,
    status: Optional[schemas.TaskStatus] = None,
    type: Optional[str] = None,
    created_after: Optional[datetime] = None,
    created_before: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100
):
    """
    Получает список задач из базы данных с возможностью фильтрации.

    :param db: Сессия базы данных.
    :param status: Фильтр по статусу задачи (если указан).
    :param type: Фильтр по типу задачи (если указан).
    :param created_after: Фильтр по дате создания.
    :param created_before: Фильтр по дате создания.
    :param skip: Количество записей, которые нужно пропустить.
    :param limit: Максимальное количество записей в ответе.
    :return: Список задач, удовлетворяющих условиям фильтрации.
    """
    query = select(models.Task)
    if status:
        query = query.filter(models.Task.status == status)
    if type:
        query = query.filter(models.Task.type == type)
    if created_after:
        query = query.filter(models.Task.created_at >= created_after)
    if created_before:
        query = query.filter(models.Task.created_at <= created_before)
    query = query.offset(skip).limit(limit)
    result = await db.execute(query)
    tasks = result.scalars().all()
    return tasks


async def get_task(
    db: Session,
    task_id: int
):
    """
    Получает задачу по её ID, используя кеширование.

    :param db: Сессия базы данных.
    :param task_id: Идентификатор задачи.
    :return: Объект задачи или None, если задача не найдена.
    """
    cache_key = f"task:{task_id}"
    cached_task = await get_cache(cache_key)
    if cached_task:
        return cached_task

    db_task = await db.get(models.Task, task_id)
    if db_task:
        await set_cache(cache_key, db_task)
    return db_task


def create_task(
    db: Session,
    task: schemas.TaskCreate
):
    """
    Создаёт новую задачу в базе данных.

    :param db: Сессия базы данных.
    :param task: Данные новой задачи.
    :return: Созданная задача.
    """
    db_task = models.Task(type=task.type)
    db.add(db_task)
    db.commit()
    db.refresh(db_task)
    return db_task


def update_task(
    db: Session,
    db_task: models.Task,
    updates: schemas.TaskUpdate
):
    """
    Обновляет задачу в базе данных.

    :param db: Сессия базы данных.
    :param db_task: Объект задачи, которую необходимо обновить.
    :param updates: Поля, которые нужно обновить.
    :return: Обновлённая задача.
    """
    for field, value in updates.dict(exclude_unset=True).items():
        setattr(db_task, field, value)
    db_task.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_task)
    return db_task


def cancel_task(
    db: Session,
    db_task: models.Task
):
    """
    Отменяет задачу, устанавливая статус CANCELED.

    :param db: Сессия базы данных.
    :param db_task: Объект задачи, которую необходимо отменить.
    :return: Обновлённая задача.
    """
    db_task.status = models.TaskStatus.CANCELED
    db_task.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(db_task)
    return db_task


async def retry_task(
    db: Session,
    db_task: models.Task
):
    """
    Перезапускает задачу, если её статус FAILED.

    :param db: Сессия базы данных.
    :param db_task: Объект задачи, которую нужно перезапустить.
    :return: Обновлённая задача.
    :raises ValueError: Если попытка перезапускается не для FAILED-задачи.
    """
    if db_task.status == models.TaskStatus.FAILED:
        db_task.status = models.TaskStatus.PENDING
        db_task.updated_at = datetime.utcnow()
        db_task.result = None
        await db.commit()
        await db.refresh(db_task)
        return db_task
    else:
        raise ValueError("Only failed tasks can be retried.")
