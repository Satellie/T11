# TODO: Реализовать цепочку корректоров:
# Сначала JamSpell, при низкой уверенности — Yandex, иначе ничего

from typing import List, Optional
from .corrector_base import ICorrector, CorrectionResult


class ChainCorrector(ICorrector):
    """Цепочка корректоров: JamSpell -> Yandex"""
    
    def __init__(self, jamspell: ICorrector, yandex: ICorrector, use_yandex_fallback: bool = True):
        self.jamspell = jamspell
        self.yandex = yandex
        self.use_yandex_fallback = use_yandex_fallback
    
    def correct(self, word: str, context_left: List[str]) -> Optional[CorrectionResult]:
        """
        Логика: сначала JamSpell, при низкой уверенности — Yandex, иначе ничего.
        """
        pass
