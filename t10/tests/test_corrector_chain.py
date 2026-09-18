"""
Тесты для corrector_chain.py (цепочка JamSpell -> Yandex).
Проверка логики фоллбэка на облачный API.
"""
import unittest
from unittest.mock import Mock, patch, MagicMock
import sys
sys.path.insert(0, '/workspace/t10')

from core.corrector_base import CorrectionResult
from core.corrector_jamspell import JamSpellCorrector
from core.corrector_yandex import YandexCorrector
from core.corrector_chain import ChainCorrector


class TestChainCorrector(unittest.TestCase):
    
    def setUp(self):
        """Создаем моки для JamSpell и Yandex корректоров"""
        self.jamspell_mock = Mock(spec=JamSpellCorrector)
        self.yandex_mock = Mock(spec=YandexCorrector)
        
        # По умолчанию фоллбэк выключен
        self.chain = ChainCorrector(
            jamspell=self.jamspell_mock,
            yandex=self.yandex_mock,
            use_cloud_fallback=False
        )
    
    def test_jamspell_returns_result_yandex_not_called(self):
        """Тест: JamSpell дал результат → Yandex не вызывается"""
        jamspell_result = CorrectionResult(
            original="привед",
            suggestion="привет",
            confidence=0.95,
            source='jamspell'
        )
        self.jamspell_mock.correct.return_value = jamspell_result
        
        result = self.chain.correct("привед", ["я"])
        
        self.assertEqual(result.suggestion, "привет")
        self.jamspell_mock.correct.assert_called_once()
        self.yandex_mock.correct.assert_not_called()
    
    def test_jamspell_none_fallback_disabled_yandex_not_called(self):
        """Тест: JamSpell вернул None, фоллбэк выключен → Yandex не вызывается"""
        self.jamspell_mock.correct.return_value = None
        self.chain.use_cloud_fallback = False
        
        result = self.chain.correct("сложноеслово", ["очень"])
        
        self.assertIsNone(result)
        self.jamspell_mock.correct.assert_called_once()
        self.yandex_mock.correct.assert_not_called()
    
    def test_jamspell_none_fallback_enabled_yandex_called(self):
        """Тест: JamSpell вернул None, фоллбэк включен → вызывается Yandex"""
        self.jamspell_mock.correct.return_value = None
        
        yandex_result = CorrectionResult(
            original="сложноеслово",
            suggestion="сложное слово",
            confidence=0.85,
            source='yandex'
        )
        self.yandex_mock.correct.return_value = yandex_result
        
        # Включаем фоллбэк
        self.chain.set_cloud_fallback_enabled(True)
        
        result = self.chain.correct("сложноеслово", ["очень"])
        
        self.assertEqual(result.suggestion, "сложное слово")
        self.assertEqual(result.source, 'yandex')
        self.jamspell_mock.correct.assert_called_once()
        self.yandex_mock.correct.assert_called_once()
    
    def test_both_return_none_final_result_none(self):
        """Тест: Оба корректора вернули None → итог None"""
        self.jamspell_mock.correct.return_value = None
        self.yandex_mock.correct.return_value = None
        
        self.chain.set_cloud_fallback_enabled(True)
        
        result = self.chain.correct("неизвестноеслово", [])
        
        self.assertIsNone(result)
        self.jamspell_mock.correct.assert_called_once()
        self.yandex_mock.correct.assert_called_once()
    
    def test_set_cloud_fallback_toggles_yandex_enabled(self):
        """Тест: set_cloud_fallback_enabled включает/выключает Yandex"""
        self.chain.set_cloud_fallback_enabled(True)
        self.assertTrue(self.chain.use_cloud_fallback)
        self.yandex_mock.set_enabled.assert_called_with(True)
        
        self.chain.set_cloud_fallback_enabled(False)
        self.assertFalse(self.chain.use_cloud_fallback)
        self.yandex_mock.set_enabled.assert_called_with(False)
    
    @patch('core.corrector_yandex.requests.Session')
    def test_yandex_correct_real_request_mocked(self, mock_session_class):
        """Тест: Реальный запрос Yandex с моком ответа API"""
        # Создаем мок сессии и ответа
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = [
            {"word": "привед", "s": ["привет", "привод"]}
        ]
        mock_session.post.return_value = mock_response
        
        # Создаем реальный YandexCorrector с включенным флагом
        yandex = YandexCorrector(enabled=True, timeout_ms=800)
        
        result = yandex.correct("привед", ["слово"])
        
        self.assertIsNotNone(result)
        self.assertEqual(result.original, "привед")
        self.assertEqual(result.suggestion, "привет")
        self.assertEqual(result.confidence, 0.85)
        self.assertEqual(result.source, 'yandex')
    
    @patch('core.corrector_yandex.requests.Session')
    def test_yandex_timeout_returns_none(self, mock_session_class):
        """Тест: Таймаут Yandex возвращает None"""
        import requests
        mock_session = Mock()
        mock_session_class.return_value = mock_session
        mock_session.post.side_effect = requests.exceptions.Timeout()
        
        yandex = YandexCorrector(enabled=True, timeout_ms=800)
        result = yandex.correct("слово", [])
        
        self.assertIsNone(result)
    
    def test_yandex_disabled_returns_none_no_network_call(self):
        """Тест: Yandex отключен → всегда None без сетевых вызовов"""
        # Используем patch на уровне класса, чтобы проверить что Session не создается
        with patch('core.corrector_yandex.requests.Session') as mock_session_class:
            yandex = YandexCorrector(enabled=False, timeout_ms=800)
            result = yandex.correct("привед", [])
            
            self.assertIsNone(result)
            mock_session_class.assert_not_called()


if __name__ == '__main__':
    unittest.main()
