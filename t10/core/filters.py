# TODO: Реализовать фильтры для игнорирования:
# URL, email, пути к файлам, числа, ники (@username), хэштеги (#tag),
# поля паролей, вставку из буфера обмена

import re
import ctypes
import ctypes.wintypes
import time
from typing import Optional

# --- Регулярные выражения ---

# URL: http(s)://, www., домены с точкой
URL_PATTERN = re.compile(
    r'(https?://|www\.)[^\s<>"]+|[a-zA-Z0-9.-]+\.(com|ru|org|net|io|gov|edu|me|info|biz)[/\w\-\.]*',
    re.IGNORECASE
)

# Email
EMAIL_PATTERN = re.compile(r'\S+@\S+\.\S+')

# Файловые пути (Windows: C:\, Linux: /home/, UNC: \\server)
PATH_PATTERN = re.compile(r'([A-Za-z]:\\|/home/|\\\\|//[\w\-]+)')

# Никнеймы и хэштеги (начинаются с @ или #)
MENTION_PATTERN = re.compile(r'^[@#]\w+')

# Числа и смешанные цифры с буквами (артикулы, коды)
NUMERIC_PATTERN = re.compile(r'.*\d.*')


def is_url(text: str) -> bool:
    """Проверить, является ли текст URL"""
    return bool(URL_PATTERN.search(text))


def is_email(text: str) -> bool:
    """Проверить, является ли текст email"""
    return bool(EMAIL_PATTERN.match(text))


def is_file_path(text: str) -> bool:
    """Проверить, является ли текст путём к файлу"""
    return bool(PATH_PATTERN.search(text))


def is_number(text: str) -> bool:
    """Проверить, является ли текст числом или содержит цифры"""
    return bool(NUMERIC_PATTERN.match(text))


def is_username(text: str) -> bool:
    """Проверить, является ли текст ником (@username)"""
    return bool(MENTION_PATTERN.match(text))


def is_hashtag(text: str) -> bool:
    """Проверить, является ли текст хэштегом (#tag)"""
    return bool(MENTION_PATTERN.match(text))


def is_too_short(text: str, min_len: int = 3) -> bool:
    """Проверить длину текста (короткие слова не исправляем)"""
    return len(text) < min_len


def should_ignore(word: str, context: Optional[dict] = None) -> bool:
    """
    Комплексная проверка: нужно ли игнорировать слово.
    Порядок проверок важен для производительности.
    """
    if is_too_short(word):
        return True
    if is_username(word) or is_hashtag(word):
        return True
    if is_number(word):
        return True
    if is_email(word):
        return True
    if is_url(word):
        return True
    if is_file_path(word):
        return True
    
    return False


# --- Детекция поля пароля ---

def is_password_field() -> bool:
    """
    Проверяет, находится ли фокус в поле ввода пароля.
    Использует Windows API (GetGUIThreadInfo, SendMessage, EM_GETPASSWORDCHAR).
    Возвращает True, если активный контрол скрывает ввод (пароль).
    """
    try:
        user32 = ctypes.windll.user32
        
        # Получаем информацию о потоке GUI
        gui_info = ctypes.wintypes.GUITHREADINFO()
        gui_info.cbSize = ctypes.sizeof(gui_info)
        
        if not user32.GetGUIThreadInfo(0, ctypes.byref(gui_info)):
            return False
            
        hwnd_focus = gui_info.hwndFocus
        if not hwnd_focus:
            return False
            
        # Проверяем тип контрола и наличие маскировки символов
        # EM_GETPASSWORDCHAR = 0x00D2
        EM_GETPASSWORDCHAR = 0x00D2
        char_mask = user32.SendMessageW(hwnd_focus, EM_GETPASSWORDCHAR, 0, 0)
        
        # Если возвращается не 0, значит поле пароля
        return char_mask != 0
        
    except Exception:
        # В случае ошибки API считаем, что это не поле пароля (fail-safe)
        return False


# --- Детекция вставки из буфера ---

class PasteDetector:
    """
    Класс для отслеживания вставки текста (Ctrl+V или Drag&Drop).
    Если за короткий промежуток времени пришло много символов без пауз — это вставка.
    """
    def __init__(self, cooldown_seconds: float = 1.0):
        self.last_paste_time = 0.0
        self.cooldown_seconds = cooldown_seconds
        self.pending_chars_count = 0
        self._time = time

    def mark_paste(self):
        """Отметить факт вставки (вызывается при детекте Ctrl+V)."""
        self.last_paste_time = self._time.time()
        self.pending_chars_count = 0

    def is_paste_cooldown(self) -> bool:
        """Проверяет, активен ли режим 'после вставки'."""
        return (self._time.time() - self.last_paste_time) < self.cooldown_seconds

    def add_char(self):
        """Увеличить счетчик символов в текущем пакете."""
        if self.is_paste_cooldown():
            self.pending_chars_count += 1

    def is_likely_paste(self, threshold: int = 5) -> bool:
        """
        Если за время cooldown пришло больше threshold символов,
        считаем это вставкой и игнорируем проверку.
        """
        if not self.is_paste_cooldown():
            return False
        return self.pending_chars_count >= threshold


# Глобальный экземпляр детектора вставки
paste_detector = PasteDetector()
