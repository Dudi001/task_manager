from pydantic import BaseModel
from datetime import datetime
from enum import Enum


class TaskStatus(str, Enum):
    PENDING = "PENDING"
    IN_PROGRESS = "IN_PROGRESS"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"
    CANCELED = "CANCELED"


class TaskBase(BaseModel):
    type: str


class TaskCreate(TaskBase):
    """
    Схема для создания задачи.
    """
    data: dict = {}


class TaskUpdate(BaseModel):
    """
    Атрибуты для обновления задачи.
    """
    status: TaskStatus = None
    result: str = None


class Task(TaskBase):
    """
    Атрибуты задачи.
    """
    id: int
    status: TaskStatus
    result: str = None
    created_at: datetime
    updated_at: datetime

    class Config:
        orm_mode = True
