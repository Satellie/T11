"""
Абстрактный интерфейс корректора орфографии.
Все корректоры (JamSpell, Yandex) реализуют этот интерфейс.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class CorrectionResult:
    """Результат коррекции слова"""
    original: str          # Исходное слово
    suggestion: str        # Предлагаемое исправление
    confidence: float      # Уверенность корректора (0.0 - 1.0)
    source: str            # 'jamspell', 'yandex'
    distance: int = 0      # Расстояние Левенштейна (для отладки/фильтрации)


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
            или не прошло защитный клапан (слишком большое расстояние Левенштейна)
        """
        pass


def levenshtein_distance(s1: str, s2: str) -> int:
    """
    Вычисляет расстояние Левенштейна между двумя строками.
    """
    if len(s1) < len(s2):
        return levenshtein_distance(s2, s1)
    
    if len(s2) == 0:
        return len(s1)
    
    previous_row = range(len(s2) + 1)
    for i, c1 in enumerate(s1):
        current_row = [i + 1]
        for j, c2 in enumerate(s2):
            insertions = previous_row[j + 1] + 1
            deletions = current_row[j] + 1
            substitutions = previous_row[j] + (c1 != c2)
            current_row.append(min(insertions, deletions, substitutions))
        previous_row = current_row
    
    return previous_row[-1]


def passes_safety_valve(original: str, suggestion: str) -> bool:
    """
    Проверка по правилу защитного клапана (п. 0.1):
    - Если расстояние Левенштейна > 3 → не исправлять
    - Если длина слова < 4 и правка меняет >= 50% букв → не исправлять
    
    Returns:
        True если исправление безопасно, False если нужно отклонить
    """
    distance = levenshtein_distance(original.lower(), suggestion.lower())
    
    # Правило 1: расстояние > 3 символа
    if distance > 3:
        return False
    
    # Правило 2: для коротких слов (< 4) правка не должна менять >= 50% букв
    # Используем >= вместо > чтобы отклонять случаи типа "он" -> "она" (1 из 2 = 50%)
    if len(original) < 4:
        change_ratio = distance / len(original)
        if change_ratio >= 0.5:
            return False
    
    return True
