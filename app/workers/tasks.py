import asyncio
import random
from math import factorial


async def process_type1(data):
    """
    Обрабатывает задачу типа 1: вычисляет факториал числа.

    :param data: Словарь, содержащий ключ 'number' с целочисленным значением.
    :return: Факториал числа.
    """
    number = data.get('number')
    if number is None or not isinstance(number, int) or number < 0:
        raise ValueError("Invalid number provided for factorial computation.")
    result = factorial(number)
    await asyncio.sleep(1)  # Симулируем длительную задачу
    return result


async def process_type2(data):
    """
    Обрабатывает задачу типа 2: переводит текст в верхний регистр.

    :param data: Словарь, содержащий ключ 'text' со строковым значением.
    :return: Строка в верхнем регистре.
    """
    text = data.get('text')
    if text is None or not isinstance(text, str):
        raise ValueError("Invalid text provided for uppercasing.")
    result = text.upper()
    await asyncio.sleep(1)
    return result


async def process_type3(data):
    """
    Обрабатывает задачу типа 3.
    Генерирует случайное число в заданном диапазоне.

    :param data: Словарь, содержащий ключи 'min' и 'max' (необязательно).
                 По умолчанию используются значения 0 и 100.
    :return: Случайное целое число в указанном диапазоне.
    """

    min_value = data.get('min', 0)
    max_value = data.get('max', 100)
    if not (isinstance(min_value, int) and isinstance(max_value, int)):
        raise ValueError(
            "Invalid range provided for random number generation."
        )
    result = random.randint(min_value, max_value)
    await asyncio.sleep(1)
    return result
