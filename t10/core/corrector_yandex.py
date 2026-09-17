# TODO: Реализовать HTTP-клиент к Yandex.Speller API
# Облачный фоллбэк для слов, в которых JamSpell не уверен

from typing import List, Optional
from .corrector_base import ICorrector, CorrectionResult


class YandexCorrector(ICorrector):
    """Корректор на основе Yandex.Speller API"""
    
    def __init__(self, timeout_ms: int = 800):
        self.timeout_ms = timeout_ms
    
    def correct(self, word: str, context_left: List[str]) -> Optional[CorrectionResult]:
        """
        Отправить запрос к Yandex.Speller API.
        Таймаут 800 мс, при ошибке сети — вернуть None.
        """
        pass
