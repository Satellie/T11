"""
Тесты для ФАЗЫ 4: casing, whitelist, blacklist.
"""

import unittest
import sys
import os

# Добавляем корень проекта в path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.casing import apply_casing


class TestCasing(unittest.TestCase):
    """Тесты сохранения регистра"""
    
    def test_all_uppercase(self):
        """Все заглавные: ПРИВЕТ -> СЛОВО (в верхнем регистре)"""
        result = apply_casing("ПРИВЕТ", "слово")
        self.assertEqual(result, "СЛОВО")
        
        result = apply_casing("HELLO", "world")
        self.assertEqual(result, "WORLD")
    
    def test_title_case(self):
        """С заглавной буквы: Привет -> Слово"""
        result = apply_casing("Привет", "слово")
        self.assertEqual(result, "Слово")
        
        result = apply_casing("Hello", "world")
        self.assertEqual(result, "World")
    
    def test_lowercase(self):
        """Все строчные: привет -> слово (suggestion остается как есть)"""
        result = apply_casing("привет", "слово")
        self.assertEqual(result, "слово")
        
        # Если suggestion пришёл в верхнем регистре от корректора - оставляем как есть
        result = apply_casing("hello", "WORLD")
        self.assertEqual(result, "WORLD")  # сохраняем регистр от корректора
    
    def test_single_char(self):
        """Одиночный символ"""
        result = apply_casing("А", "я")
        self.assertEqual(result, "Я")
        
        result = apply_casing("a", "z")
        self.assertEqual(result, "z")
    
    def test_empty_strings(self):
        """Пустые строки"""
        result = apply_casing("", "слово")
        self.assertEqual(result, "слово")
        
        result = apply_casing("слово", "")
        self.assertEqual(result, "")


class TestWhitelist(unittest.TestCase):
    """Тесты пользовательского словаря"""
    
    def setUp(self):
        import tempfile
        self.test_file = tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt')
        self.test_file.write("кложура\nспам\nURL\n")
        self.test_file.close()
        
        from core.whitelist import Whitelist
        self.whitelist = Whitelist(self.test_file.name)
    
    def tearDown(self):
        os.unlink(self.test_file.name)
    
    def test_load_from_file(self):
        """Загрузка слов из файла"""
        self.assertTrue(self.whitelist.contains("кложура"))
        self.assertTrue(self.whitelist.contains("СПАМ"))  # регистр не важен
        self.assertTrue(self.whitelist.contains("url"))
    
    def test_add_word(self):
        """Добавление нового слова"""
        self.assertFalse(self.whitelist.contains("новое"))
        self.whitelist.add("Новое")
        self.assertTrue(self.whitelist.contains("новое"))
        self.assertTrue(self.whitelist.contains("НОВОЕ"))
    
    def test_add_duplicate(self):
        """Добавление дубликата"""
        self.whitelist.add("кложура")
        self.whitelist.add("КЛОЖУРА")
        # Должно остаться одно слово
        self.assertEqual(len(self.whitelist.words), 3)  # кложура, спам, url
    
    def test_contains_case_insensitive(self):
        """Проверка без учёта регистра"""
        self.assertTrue(self.whitelist.contains("Кложура"))
        self.assertTrue(self.whitelist.contains("КЛОЖУРА"))
        self.assertTrue(self.whitelist.contains("кложура"))


class TestBlacklist(unittest.TestCase):
    """Тесты чёрного списка приложений"""
    
    def test_default_apps(self):
        """Проверка дефолтных приложений"""
        from core.blacklist import Blacklist
        bl = Blacklist()
        
        # Проверяем наличие рекомендованных приложений
        self.assertTrue(bl.contains("code.exe"))
        self.assertTrue(bl.contains("PYCHARM64.EXE"))  # регистр не важен
        self.assertTrue(bl.contains("cmd.exe"))
        self.assertTrue(bl.contains("powershell.exe"))
        self.assertTrue(bl.contains("WindowsTerminal.exe"))
    
    def test_add_remove(self):
        """Добавление и удаление приложений"""
        from core.blacklist import Blacklist
        bl = Blacklist()
        
        initial_count = len(bl.apps)
        bl.add("notepad.exe")
        self.assertTrue(bl.contains("notepad.exe"))
        self.assertEqual(len(bl.apps), initial_count + 1)
        
        bl.remove("notepad.exe")
        self.assertFalse(bl.contains("notepad.exe"))
        self.assertEqual(len(bl.apps), initial_count)
    
    def test_custom_apps(self):
        """Пользовательский список при инициализации"""
        from core.blacklist import Blacklist
        bl = Blacklist(apps=["myapp.exe", "game.exe"])
        
        self.assertTrue(bl.contains("myapp.exe"))
        self.assertTrue(bl.contains("GAME.EXE"))


if __name__ == '__main__':
    unittest.main()
