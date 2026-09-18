"""
ui/tray.py - Иконка в системном трее, меню и уведомления.
Использует pystray + Pillow.
"""
import logging
import threading
from typing import Optional, Callable

try:
    import pystray
    from PIL import Image, ImageDraw
except ImportError:
    # Заглушка для тестов без GUI
    pystray = None
    Image = None
    ImageDraw = None

logger = logging.getLogger(__name__)


class TrayIcon:
    """
    Управляет иконкой в трее, контекстным меню и всплывающими уведомлениями.
    """

    def __init__(self, 
                 on_toggle_correction: Callable[[], None],
                 on_toggle_notifications: Callable[[], None],
                 on_open_settings: Callable[[], None],
                 on_show_stats: Callable[[], None],
                 on_exit: Callable[[], None],
                 on_toggle_autostart: Callable[[], None],
                 is_correction_enabled: Callable[[], bool],
                 is_notifications_enabled: Callable[[], bool],
                 is_autostart_enabled: Callable[[], bool]):
        
        self.on_toggle_correction = on_toggle_correction
        self.on_toggle_notifications = on_toggle_notifications
        self.on_open_settings = on_open_settings
        self.on_show_stats = on_show_stats
        self.on_exit = on_exit
        self.on_toggle_autostart = on_toggle_autostart
        self.is_correction_enabled = is_correction_enabled
        self.is_notifications_enabled = is_notifications_enabled
        self.is_autostart_enabled = is_autostart_enabled
        
        self.icon: Optional[pystray.Icon] = None
        self._menu_update_event = threading.Event()

    def _create_icon_image(self) -> Image:
        """Создает простую иконку программно (синий квадрат с буквой T)."""
        if Image is None:
            return None
        
        width, height = 64, 64
        image = Image.new('RGB', (width, height), color=(0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Рисуем синий круг
        draw.ellipse([4, 4, width-4, height-4], fill=(0, 123, 255))
        
        # Рисуем букву T
        draw.rectangle([20, 15, 44, 20], fill=(255, 255, 255)) # верхняя палка
        draw.rectangle([29, 20, 35, 45], fill=(255, 255, 255)) # вертикальная палка
        
        return image

    def _build_menu(self) -> pystray.Menu:
        """Формирует контекстное меню динамически."""
        
        corr_state = "Выключить" if self.is_correction_enabled() else "Включить"
        notif_state = "Выключить" if self.is_notifications_enabled() else "Включить"
        autostart_state = "Убрать из автозагрузки" if self.is_autostart_enabled() else "Запускать с Windows"

        return pystray.Menu(
            pystray.MenuItem(f"{corr_state} коррекцию", 
                             lambda _: self._safe_call(self.on_toggle_correction),
                             default=True),
            pystray.MenuItem(f"{notif_state} уведомления", 
                             lambda _: self._safe_call(self.on_toggle_notifications)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem(autostart_state, 
                             lambda _: self._safe_call(self.on_toggle_autostart)),
            pystray.MenuItem("Настройки", 
                             lambda _: self._safe_call(self.on_open_settings)),
            pystray.MenuItem("Статистика", 
                             lambda _: self._safe_call(self.on_show_stats)),
            pystray.Menu.SEPARATOR,
            pystray.MenuItem("Выход", 
                             lambda _: self._safe_call(self.on_exit))
        )

    def _safe_call(self, callback: Callable):
        """Безопасный вызов коллбэка в отдельном потоке."""
        try:
            if callback:
                threading.Thread(target=callback, daemon=True).start()
        except Exception as e:
            logger.error(f"Ошибка при вызове действия меню: {e}")

    def show_notification(self, title: str, message: str):
        """Показывает всплывающее уведомление."""
        if not self.is_notifications_enabled():
            return
            
        if self.icon and self.icon.visible:
            try:
                # pystray.notify может работать не во всех ОС одинаково
                # Для Windows лучше использовать нативные методы, но pystray пытается абстрагировать
                self.icon.notify(message, title)
                logger.debug(f"Уведомление показано: {title} - {message}")
            except Exception as e:
                logger.warning(f"Не удалось показать уведомление через pystray: {e}")

    def run(self):
        """Запускает цикл обработки трея в отдельном потоке."""
        if pystray is None:
            logger.error("Библиотека pystray не установлена. Трей не будет работать.")
            return

        image = self._create_icon_image()
        self.icon = pystray.Icon("t10", image, "t10 - Автокорректор")
        self.icon.menu = self._build_menu
        
        # Запуск в отдельном потоке, чтобы не блокировать основной хук
        threading.Thread(target=self.icon.run, daemon=True).start()
        logger.info("Иконка в трее запущена")

    def stop(self):
        """Останавливает иконку."""
        if self.icon:
            self.icon.stop()
            logger.info("Иконка в трее остановлена")
