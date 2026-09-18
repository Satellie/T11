# TODO: Реализовать HTTP-клиент к Yandex.Speller API
# Облачный фоллбэк для слов, в которых JamSpell не уверен

import logging
import requests
from typing import List, Optional

from .corrector_base import ICorrector, CorrectionResult

logger = logging.getLogger(__name__)

YANDEX_URL = "https://speller.yandex.net/services/spellservice.json/checkText"
TIMEOUT_SEC = 0.8  # 800 мс


class YandexCorrector(ICorrector):
    """Корректор на основе Yandex.Speller API (облачный фоллбэк)"""
    
    def __init__(self, enabled: bool = False, timeout_ms: int = 800):
        self.enabled = enabled
        self.timeout_sec = timeout_ms / 1000.0
        # Не создаем сессию в __init__, чтобы можно было замокать в тестах
    
    def _get_session(self):
        """Ленивое создание сессии только при необходимости"""
        if not hasattr(self, '_session') or self._session is None:
            import requests
            self._session = requests.Session()
            self._session.headers.update({
                "User-Agent": "t10-autocorrector/1.0",
                "Content-Type": "application/x-www-form-urlencoded"
            })
        return self._session
    
    def set_enabled(self, enabled: bool):
        """Включить/выключить использование облачного API"""
        self.enabled = enabled
    
    def correct(self, word: str, context_left: List[str]) -> Optional[CorrectionResult]:
        """
        Отправить запрос к Yandex.Speller API.
        Таймаут 800 мс, при ошибке сети — вернуть None.
        
        Args:
            word: Слово для проверки
            context_left: Список предыдущих слов (контекст)
            
        Returns:
            CorrectionResult если найдено исправление, иначе None
        """
        if not self.enabled:
            logger.debug("YandexCorrector отключен в настройках")
            return None
        
        # Формируем текст для проверки: контекст (последние 2 слова) + целевое слово
        # Это нужно, чтобы API понимало контекст и лучше исправляло
        context_words = context_left[-2:] if len(context_left) >= 2 else context_left
        text_to_check = " ".join(context_words + [word])
        
        try:
            session = self._get_session()
            
            # Yandex Speller API принимает POST с параметром text
            params = {
                "text": text_to_check,
                "lang": "ru,en",
                "options": 0  # Базовые настройки
            }
            
            response = session.post(YANDEX_URL, data=params, timeout=self.timeout_sec)
            response.raise_for_status()
            
            data = response.json()
            
            # Ответ приходит списком объектов: [{"word": "...", "s": ["..."]}, ...]
            # Нам нужно найти исправление для последнего слова (нашего target word)
            if not data:
                logger.debug(f"Yandex: нет исправлений для '{word}'")
                return None
            
            last_original = word
            suggestion = None
            
            # Ищем элемент ответа, соответствующий нашему целевому слову
            for item in data:
                original_in_response = item.get("word", "")
                suggestions_list = item.get("s", [])
                
                # Сравниваем игнорируя регистр
                if original_in_response.lower() == last_original.lower():
                    if suggestions_list:
                        suggestion = suggestions_list[0]
                    break
            
            # Если прямое совпадение не найдено в цикле, проверяем последний элемент
            # (эвристика: часто ошибка бывает в последнем слове фразы)
            if suggestion is None and data:
                last_item = data[-1]
                if last_item.get("word", "").lower() == last_original.lower():
                    s_list = last_item.get("s", [])
                    if s_list:
                        suggestion = s_list[0]
            
            if suggestion and suggestion.lower() != last_original.lower():
                # Проверяем защитный клапан (расстояние Левенштейна)
                from .corrector_base import passes_safety_valve, levenshtein_distance
                distance = levenshtein_distance(last_original.lower(), suggestion.lower())
                
                if not passes_safety_valve(last_original, suggestion):
                    logger.debug(f"Yandex: защитный клапан отклонил '{last_original}' → '{suggestion}' (distance={distance})")
                    return None
                
                # Найдено исправление, отличное от исходного слова
                # Yandex не дает явной вероятности, считаем уверенность высокой (0.85)
                logger.info(f"Yandex исправление: '{last_original}' → '{suggestion}'")
                return CorrectionResult(
                    original=last_original,
                    suggestion=suggestion,
                    confidence=0.85,
                    source='yandex',
                    distance=distance
                )
            
            logger.debug(f"Yandex: предложение совпадает с оригиналом '{word}'")
            return None
            
        except requests.exceptions.Timeout:
            logger.warning(f"Yandex Speller timeout (> {self.timeout_sec}s) для слова '{word}'")
            return None
        except requests.exceptions.RequestException as e:
            logger.warning(f"Yandex Speller request failed: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error in YandexCorrector: {e}")
            return None
