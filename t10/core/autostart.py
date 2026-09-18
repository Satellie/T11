"""
Автозапуск приложения с Windows.
Создание/удаление ярлыка в папке Startup.
"""
import os
import sys
from pathlib import Path

try:
    import win32com.client
    WIN32_AVAILABLE = True
except ImportError:
    WIN32_AVAILABLE = False


def get_startup_folder() -> Path:
    """Получить путь к папке автозагрузки текущего пользователя."""
    if os.name == 'nt':
        # Путь к Startup через APPDATA
        appdata = os.environ.get('APPDATA', '')
        if appdata:
            return Path(appdata) / "Microsoft" / "Windows" / "Start Menu" / "Programs" / "Startup"
    # Fallback для не-Windows (тестирование)
    return Path.home() / ".startup"


def get_exe_path() -> str:
    """Получить путь к исполняемому файлу или скрипту."""
    if getattr(sys, 'frozen', False):
        # Запущен как .exe (PyInstaller)
        return sys.executable
    else:
        # Запущен как скрипт Python
        return sys.executable


def get_script_path() -> str:
    """Получить путь к основному скрипту main.py."""
    if getattr(sys, 'frozen', False):
        return sys.executable
    else:
        return os.path.abspath(__file__.replace('core/autostart.py', 'main.py'))


def is_autostart_enabled(app_name: str = "t10") -> bool:
    """Проверить, включен ли автозапуск."""
    if not WIN32_AVAILABLE:
        return False
    
    startup_folder = get_startup_folder()
    shortcut_path = startup_folder / f"{app_name}.lnk"
    
    return shortcut_path.exists()


def set_autostart(enabled: bool, app_name: str = "t10") -> bool:
    """
    Включить или выключить автозапуск.
    
    Args:
        enabled: True - включить, False - выключить
        app_name: Имя приложения для ярлыка
    
    Returns:
        True если успешно, False если ошибка
    """
    if not WIN32_AVAILABLE:
        print("win32com не доступен, автозапуск невозможен")
        return False
    
    try:
        startup_folder = get_startup_folder()
        startup_folder.mkdir(parents=True, exist_ok=True)
        
        shortcut_path = startup_folder / f"{app_name}.lnk"
        
        if enabled:
            # Создать ярлык
            shell = win32com.client.Dispatch("WScript.Shell")
            shortcut = shell.CreateShortCut(str(shortcut_path))
            
            # Если заморожено - указываем exe, иначе python + скрипт
            if getattr(sys, 'frozen', False):
                shortcut.Targetpath = sys.executable
                shortcut.WorkingDirectory = os.path.dirname(sys.executable)
            else:
                shortcut.Targetpath = sys.executable
                shortcut.Arguments = get_script_path()
                shortcut.WorkingDirectory = os.path.dirname(get_script_path())
            
            shortcut.Description = "t10 - системный автокорректор опечаток"
            shortcut.save()
        else:
            # Удалить ярлык
            if shortcut_path.exists():
                shortcut_path.unlink()
        
        return True
    except Exception as e:
        print(f"Ошибка настройки автозапуска: {e}")
        return False
