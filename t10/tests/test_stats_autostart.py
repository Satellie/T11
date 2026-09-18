"""
Тесты для ФАЗЫ 8: статистика и автозапуск.
"""
import unittest
import tempfile
import os
from pathlib import Path
from datetime import datetime, timedelta

# Импортируем тестируемые модули
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.stats import Stats
from core.autostart import get_startup_folder, is_autostart_enabled, set_autostart


class TestStats(unittest.TestCase):
    """Тесты для модуля статистики"""

    def setUp(self):
        # Создаем временную БД для тестов
        self.temp_db = tempfile.NamedTemporaryFile(suffix='.sqlite3', delete=False)
        self.temp_db.close()
        self.stats = Stats(db_path=self.temp_db.name)

    def tearDown(self):
        # Удаляем временную БД
        if os.path.exists(self.temp_db.name):
            os.unlink(self.temp_db.name)

    def test_init_creates_table(self):
        """Инициализация создает таблицу corrections"""
        # Просто создание объекта должно создать таблицу
        conn = self.stats._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='corrections'")
        result = cursor.fetchone()
        conn.close()
        self.assertIsNotNone(result)

    def test_record_correction(self):
        """Запись исправления работает корректно"""
        self.stats.record_correction("нашол", "нашёл", "Блокнот", "notepad.exe")
        count = self.stats.get_total_count()
        self.assertEqual(count, 1)

    def test_get_today_count_empty(self):
        """Счетчик за сегодня пуст при отсутствии записей"""
        count = self.stats.get_today_count()
        self.assertEqual(count, 0)

    def test_get_today_count_with_data(self):
        """Счетчик за сегодня показывает правильные данные"""
        # Добавляем запись с текущей датой
        self.stats.record_correction("привед", "привет", "Test", "test.exe")
        count = self.stats.get_today_count()
        self.assertEqual(count, 1)

    def test_get_week_count(self):
        """Счетчик за неделю работает корректно"""
        self.stats.record_correction("тест1", "тест2", "Test", "test.exe")
        self.stats.record_correction("еще1", "еще2", "Test", "test.exe")
        count = self.stats.get_week_count()
        self.assertEqual(count, 2)

    def test_get_total_count(self):
        """Общий счетчик работает корректно"""
        for i in range(5):
            self.stats.record_correction(f"word{i}", f"fix{i}", "Win", "proc.exe")
        count = self.stats.get_total_count()
        self.assertEqual(count, 5)

    def test_get_stats(self):
        """Метод get_stats возвращает словарь с правильными ключами"""
        self.stats.record_correction("test", "fixed", "Win", "proc.exe")
        stats = self.stats.get_stats()
        
        self.assertIn('today', stats)
        self.assertIn('week', stats)
        self.assertIn('total', stats)
        self.assertIsInstance(stats['today'], int)
        self.assertIsInstance(stats['week'], int)
        self.assertIsInstance(stats['total'], int)

    def test_undone_not_counted(self):
        """Отмененные исправления не учитываются в статистике"""
        # Добавляем запись
        self.stats.record_correction("test", "fixed", "Win", "proc.exe")
        
        # Помечаем как отмененную напрямую в БД
        conn = self.stats._get_connection()
        cursor = conn.cursor()
        cursor.execute("UPDATE corrections SET undone = 1")
        conn.commit()
        conn.close()
        
        # Счетчик должен быть 0
        count = self.stats.get_total_count()
        self.assertEqual(count, 0)


class TestAutostart(unittest.TestCase):
    """Тесты для модуля автозапуска"""

    def test_get_startup_folder_returns_path(self):
        """Функция возвращает путь к папке Startup"""
        folder = get_startup_folder()
        self.assertIsInstance(folder, Path)

    def test_autostart_functions_exist(self):
        """Функции is_autostart_enabled и set_autostart существуют"""
        # Проверяем, что функции определены (даже если win32com недоступен)
        self.assertTrue(callable(is_autostart_enabled))
        self.assertTrue(callable(set_autostart))

    def test_set_autostart_returns_bool(self):
        """Функция set_autostart возвращает boolean"""
        result = set_autostart(False, "t10_test")
        self.assertIsInstance(result, bool)


if __name__ == '__main__':
    unittest.main()
