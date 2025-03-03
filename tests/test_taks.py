from fastapi.testclient import TestClient
from app.main import app
import time


client = TestClient(app)


def test_create_task():
    response = client.post("/tasks/", json={"type": "type1"})
    assert response.status_code == 200
    assert response.json()["type"] == "type1"


def test_read_tasks():
    response = client.get("/tasks/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


def test_retry_task():
    # Создаем задачу с ошибкой
    response = client.post("/tasks/", json={"type": "type1", "data": {"number": -1}})
    task = response.json()
    task_id = task["id"]

    # Ждем обработки задачи
    time.sleep(2)

    # Проверяем, что статус FAILED
    response = client.get(f"/tasks/{task_id}")
    assert response.json()["status"] == "FAILED"

    # Повторяем задачу
    response = client.post(f"/tasks/{task_id}/retry")
    assert response.status_code == 200

    # Ждем обработки
    time.sleep(2)

    # Проверяем статус задачи после повторного выполнения
    response = client.get(f"/tasks/{task_id}")
    assert response.json()["status"] in ["PENDING", "IN_PROGRESS", "COMPLETED"]


def test_task_filtering():
    # Создаем несколько задач с разными типами и статусами
    client.post("/tasks/", json={"type": "type1", "data": {}})
    client.post("/tasks/", json={"type": "type2", "data": {}})
    client.post("/tasks/", json={"type": "type3", "data": {}})

    # Фильтрация по типу
    response = client.get("/tasks/?type=type1")
    assert response.status_code == 200
    tasks = response.json()
    assert all(task["type"] == "type1" for task in tasks)

    # Фильтрация по статусу
    response = client.get("/tasks/?status=PENDING")
    assert response.status_code == 200
    tasks = response.json()
    assert all(task["status"] == "PENDING" for task in tasks)


def test_retry_failed_task():
    # Создаем задачу, которая заведомо упадет
    response = client.post("/tasks/", json={"type": "type1", "data": {"number": -1}})
    task = response.json()
    task_id = task['id']

    # Ждем обработки задачи
    time.sleep(2)

    # Проверяем, что задача упала
    response = client.get(f"/tasks/{task_id}")
    assert response.json()["status"] == "FAILED"

    # Повторное выполнение задачи
    response = client.post(f"/tasks/{task_id}/retry")
    assert response.status_code == 200

    # Ждем обработки повторной задачи
    time.sleep(2)

    # Проверяем статус задачи
    response = client.get(f"/tasks/{task_id}")
    assert response.json()["status"] in ["PENDING", "IN_PROGRESS", "COMPLETED"]
