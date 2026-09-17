# TODO: Реализовать абстрактный интерфейс ICorrector
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class CorrectionResult:
    """Результат коррекции слова"""
    original: str
    corrected: str
    confidence: float  # Уверенность корректора (0.0 - 1.0)
    source: str  # 'jamspell', 'yandex', None


class ICorrector(ABC):
    """Абстрактный интерфейс корректора орфографии"""
    
    @abstractmethod
    def correct(self, word: str, context_left: List[str]) -> Optional[CorrectionResult]:
        """
        Исправить слово с учётом контекста.
        
        Args:
            word: Слово для проверки
            context_left: Список слов слева от текущего (контекст)
        
        Returns:
            CorrectionResult если найдено исправление, None если слово корректно
        """
        pass
