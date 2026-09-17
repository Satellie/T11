# TODO: Реализовать хоткей отката последнего исправления (Ctrl+Shift+Z по умолчанию)
# Откатывает последнее исправление, восстанавливая оригинальное слово

from typing import Optional
from .history import CorrectionEntry


class UndoManager:
    """Управление откатом последних исправлений"""
    
    def __init__(self, hotkey: str = "Ctrl+Shift+Z"):
        self.hotkey = hotkey
    
    def register_hotkey(self, callback):
        """Зарегистрировать глобальный хоткей для отката"""
        pass
    
    def undo_last(self, last_correction: CorrectionEntry):
        """Откатить последнее исправление"""
        pass
