# Реализовать счётчики исправлений за день/неделю, хранение в sqlite

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict

DB_PATH = Path(__file__).parent.parent / "data" / "stats.sqlite3"


class Stats:
    """Статистика исправлений"""

    def __init__(self, db_path: str = None):
        if db_path:
            self.db_path = Path(db_path)
        else:
            self.db_path = DB_PATH
        self._init_db()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        """Инициализировать базу данных статистики"""
        # Убедимся, что директория существует
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS corrections (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    original TEXT NOT NULL,
                    corrected TEXT NOT NULL,
                    window_title TEXT,
                    process_name TEXT,
                    undone INTEGER DEFAULT 0
                )
            """)
            conn.commit()
        finally:
            conn.close()

    def record_correction(self, original: str, corrected: str, 
                          window_title: str = "", process_name: str = ""):
        """Записать факт исправления"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute(
                """INSERT INTO corrections (original, corrected, window_title, process_name, undone)
                   VALUES (?, ?, ?, ?, 0)""",
                (original, corrected, window_title, process_name)
            )
            conn.commit()
        finally:
            conn.close()

    def get_today_count(self) -> int:
        """Получить количество исправлений за сегодня"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            today = datetime.now().strftime("%Y-%m-%d")
            cursor.execute(
                "SELECT COUNT(*) FROM corrections WHERE date(timestamp) = ? AND undone = 0",
                (today,)
            )
            result = cursor.fetchone()
            return result[0] if result else 0
        finally:
            conn.close()

    def get_week_count(self) -> int:
        """Получить количество исправлений за неделю"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
            cursor.execute(
                "SELECT COUNT(*) FROM corrections WHERE date(timestamp) >= ? AND undone = 0",
                (week_ago,)
            )
            result = cursor.fetchone()
            return result[0] if result else 0
        finally:
            conn.close()

    def get_total_count(self) -> int:
        """Получить общее количество исправлений"""
        conn = self._get_connection()
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM corrections WHERE undone = 0")
            result = cursor.fetchone()
            return result[0] if result else 0
        finally:
            conn.close()

    def get_stats(self) -> Dict[str, int]:
        """Возвращает сводку статистики"""
        return {
            "today": self.get_today_count(),
            "week": self.get_week_count(),
            "total": self.get_total_count()
        }
