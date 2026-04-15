"""
Модуль для работы с базой данных SQLite.
Хранит историю конвертаций пользователей.
"""

import sqlite3
from datetime import datetime
from typing import List, Tuple

DB_NAME = "history.db"


def init_db():
    """Создаёт таблицу history, если её нет."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            username TEXT,
            request_text TEXT NOT NULL,
            amount REAL NOT NULL,
            from_currency TEXT NOT NULL,
            to_currency TEXT NOT NULL,
            result REAL NOT NULL,
            timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
        )
    """)
    conn.commit()
    conn.close()


def add_record(user_id: int, username: str, request_text: str,
               amount: float, from_cur: str, to_cur: str, result: float):
    """Добавляет запись о конвертации в БД."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO history (user_id, username, request_text, amount, from_currency, to_currency, result)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (user_id, username, request_text, amount, from_cur.upper(), to_cur.upper(), result))
    conn.commit()
    conn.close()


def get_user_history(user_id: int, limit: int = 5) -> List[Tuple]:
    """
    Возвращает последние limit записей для данного пользователя.
    Каждая запись: (amount, from_currency, to_currency, result, timestamp)
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT amount, from_currency, to_currency, result, timestamp
        FROM history
        WHERE user_id = ?
        ORDER BY timestamp DESC
        LIMIT ?
    """, (user_id, limit))
    rows = cursor.fetchall()
    conn.close()
    return rows