# TODO: Тесты для модуля filters.py
# Проверка URL/email/путь/число/ник/хэштег фильтров

import pytest
import sys
import os

# Добавляем корень проекта в путь для импорта
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.filters import (
    is_url, is_email, is_file_path, is_number,
    is_username, is_hashtag, is_too_short, should_ignore,
    paste_detector, PasteDetector
)


def test_is_url():
    """Проверка детекции URL"""
    # Положительные тесты
    assert is_url("https://example.com") is True
    assert is_url("http://site.ru/path") is True
    assert is_url("www.google.com") is True
    assert is_url("site.com") is True
    assert is_url("test.org/page") is True
    
    # Отрицательные тесты
    assert is_url("просто текст") is False
    assert is_url("site") is False


def test_is_email():
    """Проверка детекции email"""
    # Положительные тесты
    assert is_email("test@example.com") is True
    assert is_email("user.name@domain.ru") is True
    assert is_email("a@b.co") is True
    
    # Отрицательные тесты
    assert is_email("не email") is False
    assert is_email("test@domain") is False  # нет доменной зоны


def test_is_file_path():
    """Проверка детекции путей к файлам"""
    # Windows пути
    assert is_file_path("C:\\Users\\Admin") is True
    assert is_file_path("D:\\file.txt") is True
    
    # Linux/UNC пути
    assert is_file_path("/home/user/file") is True
    assert is_file_path("\\\\server\\share") is True
    
    # Отрицательные тесты
    assert is_file_path("просто текст") is False
    assert is_file_path("file.txt") is False


def test_is_number():
    """Проверка детекции чисел и смешанных с цифрами слов"""
    # Чистые числа
    assert is_number("12345") is True
    assert is_number("0") is True
    
    # Смешанные с цифрами
    assert is_number("abc123") is True
    assert is_number("123abc") is True
    assert is_number("A1B2C3") is True
    
    # Отрицательные тесты
    assert is_number("толькобуквы") is False
    assert is_number("привет") is False


def test_is_username():
    """Проверка детекции ников (@username)"""
    # Положительные тесты
    assert is_username("@username") is True
    assert is_username("@user_123") is True
    assert is_username("@test") is True
    
    # Отрицательные тесты
    assert is_username("username") is False  # без @
    assert is_username("@") is False  # только @
    assert is_username("@ user") is False  # есть пробел


def test_is_hashtag():
    """Проверка детекции хэштегов (#tag)"""
    # Положительные тесты
    assert is_hashtag("#hashtag") is True
    assert is_hashtag("#Test123") is True
    assert is_hashtag("#новости") is True
    
    # Отрицательные тесты
    assert is_hashtag("hashtag") is False  # без #
    assert is_hashtag("#") is False  # только #
    assert is_hashtag("# tag") is False  # есть пробел


def test_is_too_short():
    """Проверка фильтра коротких слов"""
    assert is_too_short("а") is True
    assert is_too_short("аб") is True
    assert is_too_short("абв") is False  # 3 символа - уже нормально
    assert is_too_short("тест") is False
    assert is_too_short("test") is False


def test_should_ignore_comprehensive():
    """Комплексная проверка should_ignore"""
    # Игнорируемые случаи
    assert should_ignore("а") is True  # короткое
    assert should_ignore("@user") is True  # ник
    assert should_ignore("#tag") is True  # хэштег
    assert should_ignore("123abc") is True  # с цифрами
    assert should_ignore("test@example.com") is True  # email
    assert should_ignore("https://site.com") is True  # URL
    assert should_ignore("C:\\path") is True  # путь
    
    # Не игнорируемые случаи (обычные слова)
    assert should_ignore("привет") is False
    assert should_ignore("hello") is False
    assert should_ignore("нашол") is False  # опечатка - должна проверяться


def test_paste_detector():
    """Проверка детектора вставки из буфера"""
    detector = PasteDetector(cooldown_seconds=0.5)
    
    # Изначально не вставка
    assert detector.is_paste_cooldown() is False
    assert detector.is_likely_paste() is False
    
    # Отмечаем вставку
    detector.mark_paste()
    assert detector.is_paste_cooldown() is True
    
    # Добавляем символы
    for _ in range(3):
        detector.add_char()
    assert detector.is_likely_paste(threshold=5) is False  # ещё мало
    
    for _ in range(3):
        detector.add_char()
    assert detector.is_likely_paste(threshold=5) is True  # достаточно символов
