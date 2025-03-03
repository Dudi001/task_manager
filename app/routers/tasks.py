from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from app import crud, schemas
from app.dependencies import get_db
from app.workers.produser import send_task_to_queue
from typing import List, Optional
from datetime import datetime


router = APIRouter(
    prefix="/tasks",
    tags=["tasks"],
    responses={404: {"description": "Not found"}},
)


@router.get("/", response_model=List[schemas.Task])
async def read_tasks(
    status: Optional[schemas.TaskStatus] = None,
    type: Optional[str] = None,
    created_after: Optional[datetime] = None,
    created_before: Optional[datetime] = None,
    skip: int = 0,
    limit: int = 100,
    db: AsyncSession = Depends(get_db)
):
    """
    Получить список задач с возможностью фильтрации.

    :param status: Фильтр по статусу задачи.
    :param type: Фильтр по типу задачи.
    :param created_after: Фильтр по дате создания (начиная с).
    :param created_before: Фильтр по дате создания (до).
    :param skip: Количество записей, которые нужно пропустить.
    :param limit: Максимальное количество записей в ответе.
    :param db: Асинхронная сессия базы данных.
    :return: Список задач, соответствующих критериям фильтрации.
    """
    tasks = await crud.get_tasks(
        db,
        status=status,
        type=type,
        created_after=created_after,
        created_before=created_before,
        skip=skip,
        limit=limit
    )
    return tasks


@router.post("/{task_id}/retry", response_model=schemas.Task)
async def retry_task(
    task_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Повторно отправить задачу в очередь на выполнение.

    :param task_id: Идентификатор задачи.
    :param db: Асинхронная сессия базы данных.
    :return: Обновлённая задача.
    """
    db_task = await crud.get_task(db, task_id=task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    try:
        retried_task = await crud.retry_task(db, db_task=db_task)
        await send_task_to_queue({
            'id': retried_task.id,
            'type': retried_task.type,
            'data': retried_task.data
        })
        return retried_task
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))


@router.post("/", response_model=schemas.Task)
async def create_task(
    task: schemas.TaskCreate,
    db: AsyncSession = Depends(get_db)
):
    """
    Создать новую задачу и отправить её в очередь.

    :param task: Данные для создания задачи.
    :param db: Асинхронная сессия базы данных.
    :return: Созданная задача.
    """
    db_task = await crud.create_task(db=db, task=task)
    task_data = {
        'id': db_task.id,
        'type': db_task.type,
        'data': task.data
    }
    await send_task_to_queue(task_data)
    return db_task


@router.get("/{task_id}", response_model=schemas.Task)
async def read_task(
    task_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Получить информацию о задаче по её идентификатору.

    :param task_id: Идентификатор задачи.
    :param db: Асинхронная сессия базы данных.
    :return: Найденная задача.
    """
    db_task = await crud.get_task(db, task_id=task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    return db_task


@router.put("/{task_id}", response_model=schemas.Task)
async def update_task(
    task_id: int,
    task_update: schemas.TaskUpdate,
    db: AsyncSession = Depends(get_db)
):
    """
    Обновить существующую задачу.

    :param task_id: Идентификатор задачи.
    :param task_update: Данные для обновления задачи.
    :param db: Асинхронная сессия базы данных.
    :return: Обновлённая задача.
    """
    db_task = await crud.get_task(db, task_id=task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    updated_task = await crud.update_task(
        db,
        db_task=db_task,
        updates=task_update
    )
    return updated_task


@router.delete("/{task_id}", response_model=schemas.Task)
async def cancel_task(
    task_id: int,
    db: AsyncSession = Depends(get_db)
):
    """
    Отменить задачу по её идентификатору.

    :param task_id: Идентификатор задачи.
    :param db: Асинхронная сессия базы данных.
    :return: Отменённая задача.
    """
    db_task = await crud.get_task(db, task_id=task_id)
    if db_task is None:
        raise HTTPException(status_code=404, detail="Task not found")
    canceled_task = await crud.cancel_task(db, db_task=db_task)
    return canceled_task
