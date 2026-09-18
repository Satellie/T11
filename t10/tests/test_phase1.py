"""
Тесты для ФАЗЫ 1: word_buffer и language.

Критерии готовности:
- "привет мир" даёт два вызова on_word_complete с правильным контекстом
- "hello+привет" помечается как mixed и пропускается
"""

import pytest
import sys
import os

# Добавляем корень проекта в путь для импорта
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from core.language import detect_language, is_mixed_language
from core.word_buffer import WordBuffer


class TestLanguageDetection:
    """Тесты определения языка слова"""
    
    def test_russian_word(self):
        """Русское слово должно определяться как 'ru'"""
        assert detect_language("привет") == 'ru'
        assert detect_language("мир") == 'ru'
        assert detect_language("кот") == 'ru'
    
    def test_english_word(self):
        """Английское слово должно определяться как 'en'"""
        assert detect_language("hello") == 'en'
        assert detect_language("world") == 'en'
        assert detect_language("cat") == 'en'
    
    def test_mixed_language(self):
        """Смешанное слово должно определяться как 'mixed'"""
        assert detect_language("hello+привет") == 'mixed'
        assert detect_language("привет123hello") == 'mixed'
        assert detect_language("testтест") == 'mixed'
    
    def test_empty_string(self):
        """Пустая строка должна быть 'mixed'"""
        assert detect_language("") == 'mixed'
    
    def test_numbers_only(self):
        """Только цифры должны быть 'mixed'"""
        assert detect_language("12345") == 'mixed'
        assert detect_language("0") == 'mixed'
    
    def test_short_words(self):
        """Короткие слова без явного преобладания"""
        # Однобуквенные могут быть mixed из-за порога
        assert detect_language("a") == 'en'
        assert detect_language("а") == 'ru'  # кириллическая 'а'
    
    def test_is_mixed_language_helper(self):
        """Проверка вспомогательной функции is_mixed_language"""
        assert is_mixed_language("hello+привет") is True
        assert is_mixed_language("привет") is False
        assert is_mixed_language("hello") is False


class TestWordBuffer:
    """Тесты буфера слова"""
    
    def test_single_word_completion(self):
        """Завершение одного слова"""
        buffer = WordBuffer(context_size=3)
        completed_words = []
        
        def callback(word, context):
            completed_words.append((word, context.copy()))
        
        buffer.on_word_complete = callback
        
        # Набираем "привет"
        for char in "привет":
            result = buffer.add_char(char)
            assert result is None  # Пока не завершено
        
        # Завершаем пробелом
        result = buffer.add_char(' ')
        assert result is not None
        assert result[0] == "привет"
        assert result[1] == []  # Контекст пустой
        assert len(completed_words) == 1
        assert completed_words[0][0] == "привет"
    
    def test_two_words_with_context(self):
        """Два слова: второе должно иметь первое в контексте"""
        buffer = WordBuffer(context_size=3)
        completed_words = []
        
        def callback(word, context):
            completed_words.append((word, context.copy()))
        
        buffer.on_word_complete = callback
        
        # Набираем "привет "
        for char in "привет ":
            buffer.add_char(char)
        
        # Набираем "мир."
        for char in "мир.":
            buffer.add_char(char)
        
        # Должно быть два завершенных слова
        assert len(completed_words) == 2
        
        # Первое слово: "привет", контекст пустой
        assert completed_words[0][0] == "привет"
        assert completed_words[0][1] == []
        
        # Второе слово: "мир", контекст содержит "привет"
        assert completed_words[1][0] == "мир"
        assert completed_words[1][1] == ["привет"]
    
    def test_context_limit(self):
        """Контекст должен ограничиваться context_size"""
        buffer = WordBuffer(context_size=2)
        completed_words = []
        
        def callback(word, context):
            completed_words.append((word, context.copy()))
        
        buffer.on_word_complete = callback
        
        # Набираем 5 слов
        words = ["one", "two", "three", "four", "five"]
        for word in words:
            for char in word:
                buffer.add_char(char)
            buffer.add_char(' ')
        
        # Проверяем последнее слово
        last_word, last_context = completed_words[-1]
        assert last_word == "five"
        # Контекст должен содержать только последние 2 слова
        assert last_context == ["three", "four"]
    
    def test_mixed_language_skipped(self):
        """Смешанные слова должны помечаться корректно (логика фильтрации будет в filters)"""
        # Сам по себе word_buffer не фильтрует, он только передаёт слово
        # Но мы можем проверить, что слово с mixed языком корректно завершается
        buffer = WordBuffer()
        completed_words = []
        
        def callback(word, context):
            completed_words.append(word)
        
        buffer.on_word_complete = callback
        
        # Набираем смешанное слово
        for char in "hello+привет ":
            buffer.add_char(char)
        
        assert len(completed_words) == 1
        assert completed_words[0] == "hello+привет"
        # Язык этого слова определяется отдельно через detect_language
        assert detect_language(completed_words[0]) == 'mixed'
    
    def test_clear_buffer(self):
        """Очистка буфера"""
        buffer = WordBuffer()
        
        for char in "test":
            buffer.add_char(char)
        
        assert buffer.get_word() == "test"
        
        buffer.clear()
        assert buffer.get_word() == ""
    
    def test_reset_buffer(self):
        """Полный сброс буфера и контекста"""
        buffer = WordBuffer(context_size=3)
        completed_words = []
        
        def callback(word, context):
            completed_words.append((word, context.copy()))
        
        buffer.on_word_complete = callback
        
        # Набираем несколько слов
        for char in "word1 word2 ":
            buffer.add_char(char)
        
        assert len(buffer.context) > 0
        
        buffer.reset()
        
        assert buffer.current_word == ""
        assert buffer.context == []


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
