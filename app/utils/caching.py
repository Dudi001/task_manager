import os
import json
import aioredis
from pydantic.json import pydantic_encoder

REDIS_URL = os.getenv("REDIS_URL")
redis = aioredis.from_url(REDIS_URL)


async def get_cache(key: str):
    """
    Получает данные из кеша Redis по заданному ключу.

    :param key: Ключ кеша
    :return: Распакованные JSON-данные или None, если ключ не найден
    """
    data = await redis.get(key)
    if data:
        return json.loads(data)
    return None


async def set_cache(key: str, value, expire: int = 3600):
    """
    Записывает данные в кеш Redis с установленным временем жизни.

    :param key: Ключ кеша
    :param value: Данные для сохранения (объект, который можно сериализовать в JSON)
    :param expire: Время жизни ключа в секундах (по умолчанию 3600)
    """
    data = json.dumps(value, default=pydantic_encoder)
    await redis.set(key, data, ex=expire)

REDIS_URL = os.getenv("REDIS_URL")


async def get_redis():
    """
    Устанавливает и возвращает подключение к Redis.

    :return: Экземпляр подключения aioredis.Redis
    """
    return await aioredis.from_url(REDIS_URL)


async def cache_result(key: str, value: str, expire: int = 3600):
    """
    Сохраняет результат в кеш Redis.

    :param key: Ключ кеша
    :param value: Значение для сохранения (строка)
    :param expire: Время жизни ключа в секундах (по умолчанию 3600)
    """
    redis = await get_redis()
    await redis.set(key, value, ex=expire)
