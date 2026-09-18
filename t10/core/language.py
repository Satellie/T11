# TODO: Реализовать определение языка слова (ru/en/mixed)
# Приоритет: русский, затем английский

def detect_language(word: str) -> str:
    """
    Определить язык слова.
    Возвращает: 'ru', 'en', 'mixed'
    
    Эвристика:
    - Если >60% букв кириллица -> 'ru'
    - Если >60% букв латиница -> 'en'
    - Если смешанный состав или мало букв -> 'mixed' (игнорируем)
    """
    if not word:
        return 'mixed'
    
    # Извлекаем только буквы для анализа
    letters = [c for c in word if c.isalpha()]
    if not letters:
        return 'mixed'  # Нет букв (числа, символы)
    
    total = len(letters)
    cyrillic_count = sum(1 for c in letters if '\u0400' <= c <= '\u04FF')
    latin_count = sum(1 for c in letters if ('\u0041' <= c <= '\u005A') or ('\u0061' <= c <= '\u007A'))
    
    # Если есть и кириллица, и латиница -> mixed
    if cyrillic_count > 0 and latin_count > 0:
        return 'mixed'
    
    cyrillic_ratio = cyrillic_count / total
    latin_ratio = latin_count / total
    
    if cyrillic_ratio > 0.6:
        return 'ru'
    elif latin_ratio > 0.6:
        return 'en'
    else:
        return 'mixed'


def is_mixed_language(word: str) -> bool:
    """Проверить, содержит ли слово символы разных языков"""
    return detect_language(word) == 'mixed'
