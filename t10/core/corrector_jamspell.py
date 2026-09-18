"""
HTTP-клиент к JamSpell сервису, запущенному в WSL2.
Поддерживает русский (порт 8080) и английский (порт 8081) языки.
"""
import logging
from typing import List, Optional
import requests

from .corrector_base import ICorrector, CorrectionResult, levenshtein_distance, passes_safety_valve

logger = logging.getLogger(__name__)

# Конфигурация серверов JamSpell
JAMSPELL_RU_URL = "http://127.0.0.1:8080/fix"
JAMSPELL_EN_URL = "http://127.0.0.1:8081/fix"
TIMEOUT_SECONDS = 0.5  # 500 мс таймаут на запрос


class JamSpellCorrector(ICorrector):
    """
    Корректор на основе JamSpell через HTTP API.
    Автоматически выбирает порт в зависимости от языка слова.
    """
    
    def __init__(self, ru_url: str = JAMSPELL_RU_URL, en_url: str = JAMSPELL_EN_URL, timeout: float = TIMEOUT_SECONDS):
        self.ru_url = ru_url
        self.en_url = en_url
        self.timeout = timeout
    
    def _get_url_for_language(self, language: str) -> str:
        """Возвращает URL сервера для указанного языка."""
        if language == 'en':
            return self.en_url
        return self.ru_url  # По умолчанию русский
    
    def correct(self, word: str, context_left: List[str]) -> Optional[CorrectionResult]:
        """
        Исправить слово используя JamSpell.
        
        Args:
            word: Слово для проверки
            context_left: Список слов слева (контекст)
        
        Returns:
            CorrectionResult если найдено исправление и оно прошло защитный клапан,
            None если слово корректно или исправление слишком радикальное
        """
        # Определяем язык слова
        has_cyrillic = any('\u0400' <= c <= '\u04FF' for c in word)
        has_latin = any('a' <= c.lower() <= 'z' for c in word)
        
        if has_cyrillic and has_latin:
            # Смешанный язык - не исправляем
            logger.debug(f"Слово '{word}' содержит смешанный язык, пропускаем")
            return None
        
        language = 'ru' if has_cyrillic else 'en'
        url = self._get_url_for_language(language)
        
        # Формируем контекст для JamSpell
        # Передаём последние 2-3 слова + текущее слово одной строкой
        context_words = context_left[-2:] if len(context_left) >= 2 else context_left
        text_to_check = ' '.join(context_words + [word])
        
        try:
            # JamSpell web_server принимает GET запрос с параметром text
            response = requests.get(
                url,
                params={'text': text_to_check},
                timeout=self.timeout,
                headers={'Content-Type': 'application/json'}
            )
            
            if response.status_code != 200:
                logger.warning(f"JamSpell вернул статус {response.status_code}")
                return None
            
            # Парсим ответ
            # JamSpell возвращает исправленный текст целиком
            corrected_text = response.text.strip()
            
            # Разбиваем на слова
            original_words = context_words + [word]
            corrected_words = corrected_text.split()
            
            # Если количество слов не совпадает, JamSpell мог объединить/разделить слова
            # В этом случае берём последнее слово исправленного текста как кандидат
            if len(corrected_words) != len(original_words):
                if not corrected_words:
                    return None
                suggestion = corrected_words[-1]
            else:
                # Количество слов совпадает - берём слово на той же позиции
                suggestion = corrected_words[-1]
            
            # Если слово не изменилось - всё хорошо
            if suggestion.lower() == word.lower():
                logger.debug(f"Слово '{word}' корректно")
                return None
            
            # Проверяем защитный клапан
            distance = levenshtein_distance(word.lower(), suggestion.lower())
            if not passes_safety_valve(word, suggestion):
                logger.info(f"Слово '{word}' -> '{suggestion}' отклонено защитным клапаном (distance={distance})")
                return None
            
            # Оцениваем уверенность (упрощённо: чем меньше расстояние, тем выше уверенность)
            # JamSpell сам ранжирует кандидатов, поэтому top-1 имеет высокую уверенность
            confidence = max(0.5, 1.0 - (distance / max(len(word), len(suggestion))))
            
            result = CorrectionResult(
                original=word,
                suggestion=suggestion,
                confidence=confidence,
                source='jamspell',
                distance=distance
            )
            
            logger.info(f"JamSpell: '{word}' -> '{suggestion}' (confidence={confidence:.2f}, distance={distance})")
            return result
            
        except requests.exceptions.Timeout:
            logger.warning(f"Таймаут запроса к JamSpell ({self.timeout}с)")
            return None
        except requests.exceptions.ConnectionError:
            logger.warning("Не удалось подключиться к JamSpell сервису (проверьте, запущен ли WSL2 сервис)")
            return None
        except Exception as e:
            logger.error(f"Ошибка при запросе к JamSpell: {e}")
            return None
