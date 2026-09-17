# t10 — Системный автокорректор опечаток для Windows
# Точка входа, оркестрация потоков

import logging
import sys
from pathlib import Path

# Настройка логирования
LOG_FILE = Path(__file__).parent / "t10.log"
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE, encoding="utf-8"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


def main():
    """
    ФАЗА 0: Hello World хук.
    
    Запускает низкоуровневый перехват клавиатуры и логирует все нажатия.
    Цель: доказать, что хук стабильно ловит ввод системно (в любом окне)
    и не блокирует систему.
    """
    logger.info("=" * 50)
    logger.info("t10 - запуск (ФАЗА 0: Hello World хук)")
    logger.info("=" * 50)
    
    from core.hook import KeyboardHook
    
    # Callback для логирования нажатий
    def on_key_press(char: str):
        """Вызывается при каждом нажатии печатной клавиши."""
        logger.info(f"Ввод: '{char}'")
    
    # Создаём и запускаем хук
    hook = KeyboardHook(callback=on_key_press)
    
    logger.info("Нажмите Ctrl+C в этом окне для выхода")
    
    try:
        hook.start()
        
        # Держим основной поток живым
        import time
        while True:
            time.sleep(1)
            
    except KeyboardInterrupt:
        logger.info("Получен сигнал остановки (Ctrl+C)")
    finally:
        hook.stop()
        logger.info("t10 - завершение работы")


if __name__ == "__main__":
    main()
