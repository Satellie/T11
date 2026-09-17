# TODO: Реализовать окно настроек (tkinter, без тяжёлых зависимостей)
# Управление чёрным списком, хоткеями, включением/выключением уведомлений

import tkinter as tk
from typing import Optional


class SettingsWindow:
    """Окно настроек приложения"""
    
    def __init__(self, parent: Optional[tk.Tk] = None):
        self.parent = parent
    
    def show(self):
        """Показать окно настроек"""
        pass
    
    def hide(self):
        """Скрыть окно настроек"""
        pass
