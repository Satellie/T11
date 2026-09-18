# TODO: Реализовать цепочку корректоров:
# Сначала JamSpell, при низкой уверенности — Yandex, иначе ничего

import logging
from typing import List, Optional

from .corrector_base import ICorrector, CorrectionResult
from .corrector_jamspell import JamSpellCorrector
from .corrector_yandex import YandexCorrector

logger = logging.getLogger(__name__)


class ChainCorrector(ICorrector):
    """Цепочка корректоров: JamSpell -> Yandex (фоллбэк)"""
    
    def __init__(self, jamspell: JamSpellCorrector, yandex: YandexCorrector, use_cloud_fallback: bool = False):
        self.jamspell = jamspell
        self.yandex = yandex
        self.use_cloud_fallback = use_cloud_fallback
    
    def set_cloud_fallback_enabled(self, enabled: bool):
        """Включить/выключить использование облачного фоллбэка"""
        self.use_cloud_fallback = enabled
        if enabled:
            self.yandex.set_enabled(True)
            logger.info("Облачный фоллбэк (Yandex) включен")
        else:
            self.yandex.set_enabled(False)
            logger.debug("Облачный фоллбэк (Yandex) выключен")
    
    def correct(self, word: str, context_left: List[str]) -> Optional[CorrectionResult]:
        """
        Логика цепочки:
        1. Спросить JamSpell.
        2. Если JamSpell вернул None (не уверен / сработал защитный клапан) 
           И включен флаг use_cloud_fallback → спросить Yandex.
        3. Если и Yandex ничего не дал → не исправлять, залогировать.
        
        Args:
            word: Слово для проверки
            context_left: Список предыдущих слов (контекст)
            
        Returns:
            CorrectionResult если найдено исправление, иначе None
        """
        # Шаг 1: Пробуем JamSpell (локальный, быстрый, приватный)
        result = self.jamspell.correct(word, context_left)
        
        if result is not None:
            logger.debug(f"JamSpell исправил '{word}' → '{result.suggestion}' (confidence={result.confidence})")
            return result
        
        # JamSpell не дал результата (None означает: нет исправления или сработал защитный клапан)
        logger.debug(f"JamSpell не дал исправления для '{word}'")
        
        # Шаг 2: Если включен облачный фоллбэк, пробуем Yandex
        if self.use_cloud_fallback:
            logger.debug(f"Попытка облачного фоллбэка (Yandex) для '{word}'")
            yandex_result = self.yandex.correct(word, context_left)
            
            if yandex_result is not None:
                logger.info(f"Yandex исправил '{word}' → '{yandex_result.suggestion}' (fallback)")
                return yandex_result
            
            logger.debug(f"Yandex также не дал исправления для '{word}'")
        else:
            logger.debug(f"Облачный фоллбэк отключен, пропускаем Yandex для '{word}'")
        
        # Шаг 3: Ничего не найдено
        logger.debug(f"Ни один корректор не дал исправления для '{word}'")
        return None
