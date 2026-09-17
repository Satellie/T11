# TODO: Реализовать кольцевой буфер последних 500 исправлений
# Используется для отката (undo) и статистики

from collections import deque
from dataclasses import dataclass
from typing import Optional, List


@dataclass
class CorrectionEntry:
    """Запись об исправлении"""
    original: str
    corrected: str
    timestamp: float
    app_name: str


class History:
    """Кольцевой буфер истории исправлений"""
    
    def __init__(self, max_size: int = 500):
        self.buffer = deque(maxlen=max_size)
    
    def add(self, entry: CorrectionEntry):
        """Добавить запись в историю"""
        pass
    
    def get_last(self, count: int = 1) -> List[CorrectionEntry]:
        """Получить последние N записей"""
        pass
    
    def clear(self):
        """Очистить историю"""
        pass
