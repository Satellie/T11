"""
Состояние "текущее набираемое слово".
Буферизация символов до разделителя (пробел, знак препинания, Enter).
"""

from typing import Callable, List, Optional
from .language import detect_language


# Символы, завершающие слово
WORD_DELIMITERS = {
    ' ', '\t', '\n', '\r',  # Пробельные символы
    '.', ',', '!', '?', ';', ':',  # Знаки препинания
    '"', "'", '(', ')', '[', ']', '{', '}',  # Скобки и кавычки
    '-', '—', '–',  # Тире
    '/', '\\', '|',  # Разделители путей
    '@', '#', '$', '%', '^', '&', '*', '_', '+', '=', '<', '>', '~', '`'
}


class WordBuffer:
    def __init__(self, context_size: int = 3):
        """
        Инициализировать буфер слова.
        
        Args:
            context_size: Количество предыдущих слов для контекста.
        """
        self.current_word = ""
        self.context: List[str] = []  # Последние завершенные слова
        self.context_size = context_size
        self.on_word_complete: Optional[Callable[[str, List[str]], None]] = None
    
    def add_char(self, char: str) -> Optional[tuple]:
        """
        Добавить символ в текущее слово.
        
        Если символ является разделителем, завершает текущее слово и вызывает callback.
        
        Args:
            char: Символ для добавления.
            
        Returns:
            Кортеж (word, context) если слово завершено, иначе None.
        """
        if char in WORD_DELIMITERS:
            # Завершаем текущее слово
            if self.current_word:
                word = self.current_word
                context = self.context[-self.context_size:] if self.context else []
                
                # Добавляем слово в контекст
                self.context.append(word)
                if len(self.context) > self.context_size * 2:  # Храним больше для истории
                    self.context = self.context[-self.context_size * 2:]
                
                self.current_word = ""
                
                # Вызываем callback если установлен
                if self.on_word_complete:
                    self.on_word_complete(word, context)
                
                return (word, context)
            return None
        else:
            # Добавляем символ к текущему слову
            self.current_word += char
            return None
    
    def clear(self):
        """Очистить буфер текущего слова"""
        self.current_word = ""
    
    def get_word(self) -> str:
        """Получить текущее слово"""
        return self.current_word
    
    def reset(self):
        """Полный сброс буфера и контекста"""
        self.current_word = ""
        self.context = []
