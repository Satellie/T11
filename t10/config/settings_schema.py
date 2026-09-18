# Схема настроек приложения t10
from dataclasses import dataclass, field
from typing import List


@dataclass
class SettingsSchema:
    """Схема настроек приложения t10"""
    
    # Общие настройки
    enable_correction: bool = True  # Глобальное включение/выключение коррекции
    enable_notifications: bool = True  # Показывать уведомления при исправлениях
    language_priority: str = "ru"  # Приоритетный язык: "ru" или "en"
    
    # Хоткеи
    hotkey_undo: str = "Ctrl+Shift+Z"  # Хоткей для отката последнего исправления
    
    # Облачный фоллбэк (приватность)
    use_cloud_fallback: bool = False  # Разрешить отправку текста в Яндекс (Yandex Speller API)
    
    # Черный список приложений (процессы, где коррекция отключена)
    blacklist_apps: List[str] = field(default_factory=lambda: [
        "code.exe",  # VS Code
        "pycharm64.exe",  # PyCharm
        "cmd.exe",  # Командная строка Windows
        "powershell.exe",  # PowerShell
        "WindowsTerminal.exe",  # Терминал Windows
    ])
    
    # Настройки JamSpell
    jamspell_port_ru: int = 8080  # Порт JamSpell для русского языка (WSL2)
    jamspell_port_en: int = 8081  # Порт JamSpell для английского языка (WSL2)
    jamspell_timeout_ms: int = 500  # Таймаут запроса к JamSpell (мс)
    
    # Настройки Yandex Speller
    yandex_timeout_ms: int = 800  # Таймаут запроса к Yandex (мс)
    
    # Пороги защитного клапана (Левенштейн)
    levenshtein_max_distance: int = 3  # Максимальное расстояние Левенштейна для автоисправления
    short_word_min_length: int = 4  # Слова короче этого не исправляются (защита от ложных срабатываний)
    
    # История и статистика
    history_max_size: int = 500  # Максимальный размер истории исправлений

