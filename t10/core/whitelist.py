"""
Модуль управления пользовательским словарём исключений (whitelist).

Слова из этого списка не отправляются на коррекцию.
Файл data/user_dictionary.txt растёт по мере использования.
"""

import os
import logging

logger = logging.getLogger(__name__)

class Whitelist:
    """Управление пользовательским словарём исключений"""
    
    def __init__(self, filepath: str = "data/user_dictionary.txt"):
        self.filepath = filepath
        self.words = set()
        self._load()
    
    def _load(self):
        """Загрузить слова из файла"""
        if not os.path.exists(self.filepath):
            logger.debug(f"Whitelist файл не найден: {self.filepath}")
            return
        
        try:
            with open(self.filepath, 'r', encoding='utf-8') as f:
                for line in f:
                    word = line.strip().lower()
                    if word:
                        self.words.add(word)
            logger.debug(f"Загружено {len(self.words)} слов из whitelist")
        except Exception as e:
            logger.error(f"Ошибка загрузки whitelist: {e}")
    
    def add(self, word: str) -> bool:
        """
        Добавить слово в whitelist.
        
        Args:
            word: Слово для добавления (регистр игнорируется).
        
        Returns:
            True если слово было добавлено, False если уже существовало.
        """
        word_lower = word.lower()
        if word_lower in self.words:
            return False
        
        self.words.add(word_lower)
        self._save_word(word_lower)
        logger.debug(f"Добавлено слово в whitelist: {word}")
        return True
    
    def _save_word(self, word: str):
        """Дописать одно слово в файл"""
        try:
            os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
            with open(self.filepath, 'a', encoding='utf-8') as f:
                f.write(word + '\n')
        except Exception as e:
            logger.error(f"Ошибка записи слова в whitelist: {e}")
    
    def contains(self, word: str) -> bool:
        """
        Проверить, есть ли слово в whitelist.
        
        Args:
            word: Слово для проверки (регистр игнорируется).
        
        Returns:
            True если слово есть в списке, False иначе.
        """
        return word.lower() in self.words
    
    def save(self):
        """Сохранить весь whitelist в файл (перезапись)"""
        try:
            os.makedirs(os.path.dirname(self.filepath), exist_ok=True)
            with open(self.filepath, 'w', encoding='utf-8') as f:
                for word in sorted(self.words):
                    f.write(word + '\n')
            logger.debug(f"Сохранено {len(self.words)} слов в whitelist")
        except Exception as e:
            logger.error(f"Ошибка сохранения whitelist: {e}")
