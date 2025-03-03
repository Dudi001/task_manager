from fastapi import FastAPI
from .routers import tasks


app = FastAPI(
    title="Task Manager API",
    description="API для управления задачами",
    version="1.0.0",
)

app.include_router(tasks.router)
