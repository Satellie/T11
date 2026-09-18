"""
Тесты для ФАЗЫ 5: История исправлений и откат (undo).
"""
import unittest
import tempfile
import os
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

# Добавляем путь к модулям
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))

from core.history import CorrectionHistory, CorrectionRecord


class TestCorrectionHistory(unittest.TestCase):
    """Тесты для истории исправлений."""
    
    def setUp(self):
        """Создание временной БД для каждого теста."""
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.sqlite3')
        self.temp_db.close()
        self.db_path = Path(self.temp_db.name)
        self.history = CorrectionHistory(db_path=self.db_path)
    
    def tearDown(self):
        """Удаление временной БД."""
        try:
            os.unlink(self.db_path)
        except Exception:
            pass
    
    def test_add_record(self):
        """Тест добавления записи в историю."""
        self.history.add("привед", "привет", "Блокнот", "notepad.exe")
        
        last = self.history.get_last()
        self.assertIsNotNone(last)
        self.assertEqual(last.original, "привед")
        self.assertEqual(last.corrected, "привет")
        self.assertFalse(last.undone)
    
    def test_ring_buffer_limit(self):
        """Тест кольцевого буфера: старые записи вытесняются."""
        # Добавляем 550 записей (больше лимита 500)
        for i in range(550):
            self.history.add(f"word{i}", f"fixed{i}", "Window", "app.exe")
        
        # Проверяем, что в буфере не больше 500
        all_records = self.history.get_all()
        self.assertLessEqual(len(all_records), 500)
        
        # Первая добавленная запись должна быть утеряна
        # Последняя должна быть на месте
        last = self.history.get_last()
        self.assertEqual(last.original, "word549")
    
    def test_get_last_undone(self):
        """Тест получения последней НЕ отмененной записи."""
        self.history.add("word1", "fix1", "Win", "app.exe")
        self.history.add("word2", "fix2", "Win", "app.exe")
        self.history.add("word3", "fix3", "Win", "app.exe")
        
        # Получаем последнюю
        last = self.history.get_last()
        self.assertEqual(last.original, "word3")
        
        # Отменяем её
        self.history.mark_undone(last)
        
        # Теперь последняя должна быть word2
        last = self.history.get_last()
        self.assertEqual(last.original, "word2")
    
    def test_mark_undone(self):
        """Тест пометки записи как отмененной."""
        self.history.add("test", "fixed", "Window", "app.exe")
        
        record = self.history.get_last()
        self.assertFalse(record.undone)
        
        self.history.mark_undone(record)
        
        # Проверяем, что запись помечена
        self.assertTrue(record.undone)
        
        # get_last() должен вернуть None (других записей нет)
        self.assertIsNone(self.history.get_last())
    
    def test_persistence(self):
        """Тест сохранения и загрузки из БД."""
        # Добавляем записи
        self.history.add("orig1", "corr1", "Title1", "proc1.exe")
        self.history.add("orig2", "corr2", "Title2", "proc2.exe")
        
        # Создаем новый инстанс с той же БД
        new_history = CorrectionHistory(db_path=self.db_path)
        
        # Проверяем, что данные загрузились
        last = new_history.get_last()
        self.assertEqual(last.original, "orig2")
        self.assertEqual(last.corrected, "corr2")
        self.assertEqual(last.window_title, "Title2")
        self.assertEqual(last.process_name, "proc2.exe")
    
    def test_clear(self):
        """Тест очистки истории."""
        self.history.add("word1", "fix1", "Win", "app.exe")
        self.history.add("word2", "fix2", "Win", "app.exe")
        
        self.history.clear()
        
        self.assertIsNone(self.history.get_last())
        self.assertEqual(len(self.history.get_all()), 0)


class TestUndoManager(unittest.TestCase):
    """Тесты для менеджера отката (только логика, без Windows API)."""
    
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False, suffix='.sqlite3')
        self.temp_db.close()
        self.db_path = Path(self.temp_db.name)
        self.history = CorrectionHistory(db_path=self.db_path)
    
    def tearDown(self):
        try:
            os.unlink(self.db_path)
        except Exception:
            pass
    
    @patch('core.undo.WINDOWS_AVAILABLE', False)
    def test_undo_manager_creation(self):
        """Тест создания UndoManager без Windows API."""
        from core.undo import UndoManager
        
        undo_mgr = UndoManager(self.history, hotkey="Ctrl+Shift+Z")
        
        self.assertEqual(undo_mgr.hotkey, "Ctrl+Shift+Z")
        self.assertEqual(undo_mgr.history, self.history)
    
    @patch('core.undo.WINDOWS_AVAILABLE', False)
    def test_hotkey_parsing(self):
        """Тест парсинга хоткея."""
        from core.undo import UndoManager
        
        undo_mgr = UndoManager(self.history, hotkey="Ctrl+Alt+Z")
        
        # Проверяем, что модификаторы распарсились
        self.assertIsNotNone(undo_mgr.modifiers)
        self.assertIsNotNone(undo_mgr.vk_code)
    
    def test_empty_history_no_undo(self):
        """Тест: при пустой истории откат невозможен."""
        last = self.history.get_last()
        self.assertIsNone(last)


if __name__ == '__main__':
    unittest.main()
