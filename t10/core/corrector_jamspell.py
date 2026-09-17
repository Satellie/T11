# TODO: Реализовать HTTP-клиент к JamSpell (WSL2 сервис)
# JamSpell работает как отдельный локальный HTTP-сервис в WSL2 на порту 8080

from typing import List, Optional
from .corrector_base import ICorrector, CorrectionResult


class JamSpellCorrector(ICorrector):
    """Корректор на основе JamSpell через HTTP"""
    
    def __init__(self, host: str = "127.0.0.1", port: int = 8080, timeout_ms: int = 500):
        self.host = host
        self.port = port
        self.timeout_ms = timeout_ms
    
    def correct(self, word: str, context_left: List[str]) -> Optional[CorrectionResult]:
        """
        Отправить запрос к JamSpell сервису в WSL2.
        Таймаут 300-500 мс, при ошибке сети — вернуть None.
        """
        pass
