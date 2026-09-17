# TODO: Реализовать счётчики исправлений за день/неделю, хранение в sqlite

import sqlite3
from datetime import datetime
from typing import Dict, Optional


class Stats:
    """Статистика исправлений"""
    
    def __init__(self, db_path: str = "data/stats.sqlite3"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Инициализировать базу данных статистики"""
        pass
    
    def record_correction(self, source: str):
        """Записать факт исправления"""
        pass
    
    def get_today_count(self) -> int:
        """Получить количество исправлений за сегодня"""
        pass
    
    def get_week_count(self) -> int:
        """Получить количество исправлений за неделю"""
        pass
    
    def get_total_count(self) -> int:
        """Получить общее количество исправлений"""
        pass
