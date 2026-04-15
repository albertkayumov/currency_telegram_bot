"""
Модуль для работы с внешним API курсов валют.
Используем бесплатный сервис exchangerate-api.com (или любой другой).
"""

import requests
from typing import Optional, Dict

# Базовый URL API (бесплатный тариф без ключа)
BASE_URL = "https://api.exchangerate-api.com/v4/latest/"


def get_exchange_rates(base_currency: str = "USD") -> Optional[Dict[str, float]]:
    """
    Получает актуальные курсы валют относительно базовой валюты.

    :param base_currency: трёхбуквенный код базовой валюты (например, 'USD')
    :return: словарь вида {'USD': 1.0, 'EUR': 0.92, ...} или None при ошибке
    """
    url = f"{BASE_URL}{base_currency.upper()}"
    try:
        response = requests.get(url, timeout=5)
        response.raise_for_status()  # выбросит исключение при статусе 4xx/5xx
        data = response.json()
        return data.get("rates")
    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе к API: {e}")
        return None


def convert_currency(amount: float, from_currency: str, to_currency: str) -> Optional[float]:
    """
    Конвертирует сумму из одной валюты в другую.

    :param amount: сумма в исходной валюте
    :param from_currency: код исходной валюты
    :param to_currency: код целевой валюты
    :return: сконвертированная сумма или None при ошибке
    """
    rates = get_exchange_rates(from_currency)
    if not rates:
        return None
    rate = rates.get(to_currency.upper())
    if rate is None:
        return None
    return amount * rate