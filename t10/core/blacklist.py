"""
Модуль управления чёрным списком приложений (где коррекция отключена).

Использует pywin32 и psutil для определения имени активного процесса.
Проверка должна выполняться ПЕРЕД всей остальной логикой коррекции.
"""

import logging
from typing import Optional

try:
    import win32gui
    import win32process
    import psutil
    WINDOWS_AVAILABLE = True
except ImportError:
    # Для тестирования на Linux или без зависимостей
    WINDOWS_AVAILABLE = False
    win32gui = None
    win32process = None
    psutil = None

logger = logging.getLogger(__name__)

# Рекомендованные приложения по умолчанию (IDE, консоли, терминалы)
DEFAULT_BLACKLIST = [
    'code.exe',           # VS Code
    'pycharm64.exe',      # PyCharm
    'idea64.exe',         # IntelliJ IDEA
    'webstorm64.exe',     # WebStorm
    'cmd.exe',            # Command Prompt
    'powershell.exe',     # PowerShell
    'pwsh.exe',           # PowerShell Core
    'WindowsTerminal.exe', # Windows Terminal
    'wt.exe',             # Windows Terminal alias
    'conhost.exe',        # Console Host
]


class Blacklist:
    """Управление списком процессов, где коррекция отключена"""
    
    def __init__(self, apps: list = None):
        """
        Инициализировать чёрный список.
        
        Args:
            apps: Список имён процессов (.exe) для добавления в чёрный список.
        """
        self.apps = set()
        # Добавляем дефолтные приложения
        for app in DEFAULT_BLACKLIST:
            self.apps.add(app.lower())
        # Добавляем пользовательские
        if apps:
            for app in apps:
                self.apps.add(app.lower())
        logger.debug(f"Чёрный список инициализирован с {len(self.apps)} приложениями")
    
    def add(self, app_name: str):
        """
        Добавить приложение в чёрный список.
        
        Args:
            app_name: Имя процесса (например, 'notepad.exe').
        """
        self.apps.add(app_name.lower())
        logger.debug(f"Добавлено в чёрный список: {app_name}")
    
    def remove(self, app_name: str):
        """
        Удалить приложение из чёрного списка.
        
        Args:
            app_name: Имя процесса для удаления.
        """
        app_lower = app_name.lower()
        if app_lower in self.apps:
            self.apps.remove(app_lower)
            logger.debug(f"Удалено из чёрного списка: {app_name}")
            return True
        return False
    
    def contains(self, app_name: str) -> bool:
        """
        Проверить, есть ли приложение в чёрном списке.
        
        Args:
            app_name: Имя процесса для проверки.
        
        Returns:
            True если приложение в чёрном списке, False иначе.
        """
        return app_name.lower() in self.apps
    
    def is_current_process_blacklisted(self) -> bool:
        """
        Проверить, находится ли текущий активный процесс в чёрном списке.
        
        Returns:
            True если текущий процесс в чёрном списке, False иначе.
        """
        current_process = self.get_current_process_name()
        if current_process is None:
            return False
        return self.contains(current_process)
    
    @staticmethod
    def get_current_process_name() -> Optional[str]:
        """
        Получить имя текущего активного процесса (окна в фокусе).
        
        Returns:
            Имя процесса (.exe) или None если не удалось определить.
        """
        if not WINDOWS_AVAILABLE:
            logger.warning("Windows API недоступны, невозможно определить процесс")
            return None
        
        try:
            # Получаем окно в фокусе
            hwnd = win32gui.GetForegroundWindow()
            if not hwnd:
                return None
            
            # Получаем PID процесса, которому принадлежит окно
            _, pid = win32process.GetWindowThreadProcessId(hwnd)
            
            # Получаем имя процесса по PID
            process = psutil.Process(pid)
            process_name = process.name()
            
            return process_name
        except Exception as e:
            logger.debug(f"Не удалось получить имя процесса: {e}")
            return None
