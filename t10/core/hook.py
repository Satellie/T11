"""
Низкоуровневый перехват клавиатуры через Windows API (ctypes).

Использует SetWindowsHookExA с WH_KEYBOARD_LL для глобального перехвата
нажатий клавиш. Не использует библиотеку 'keyboard' из-за проблем со
стабильностью и кириллицей.

Этот модуль только ловит события и передаёт их в callback. Вся логика
обработки (буферизация слов, коррекция) вынесена в другие модули.
"""

import ctypes
from ctypes import wintypes
import threading
import logging
from typing import Callable, Optional

# Настройка логирования
logger = logging.getLogger(__name__)

# === Константы Windows API ===
WH_KEYBOARD_LL = 13
WM_KEYDOWN = 0x0100
WM_SYSKEYDOWN = 0x0104

# Структура KBDLLHOOKSTRUCT из WinAPI
class KBDLLHOOKSTRUCT(ctypes.Structure):
    _fields_ = [
        ("vkCode", wintypes.DWORD),
        ("scanCode", wintypes.DWORD),
        ("flags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(wintypes.ULONG)),
    ]

# Тип функции хука
HOOKPROC = ctypes.CFUNCTYPE(
    wintypes.LPARAM,  # возвращаемое значение (LRESULT)
    wintypes.INT,     # nCode
    wintypes.WPARAM,  # wParam (код сообщения)
    ctypes.POINTER(KBDLLHOOKSTRUCT)  # lParam (структура с данными клавиши)
)


class KeyboardHook:
    """
    Низкоуровневый перехватчик клавиатуры.
    
    Использует SetWindowsHookExA для установки глобального хука.
    Поток хука работает асинхронно, не блокируя основной поток приложения.
    """
    
    def __init__(self, callback: Callable[[str], None]):
        """
        Инициализирует хук.
        
        Args:
            callback: Функция, вызываемая при нажатии печатной клавиши.
                      Получает символ (строку) или пустую строку для непечатных.
        """
        self.callback = callback
        self.hook_handle = None
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._hook_proc: Optional[HOOKPROC] = None
        
        # Загружаем библиотеки
        self.user32 = ctypes.windll.user32
        self.kernel32 = ctypes.windll.kernel32
        
    def _low_level_handler(self, n_code: int, w_param: int, l_param: int) -> int:
        """
        Внутренний обработчик хука. Вызывается Windows при каждом нажатии.
        
        Возвращает 0 для продолжения цепочки хуков, или 1 для блокировки события.
        """
        if n_code >= 0:
            # Проверяем тип события (нажатие клавиши)
            if w_param in (WM_KEYDOWN, WM_SYSKEYDOWN):
                struct_ptr = ctypes.cast(l_param, ctypes.POINTER(KBDLLHOOKSTRUCT))
                vk_code = struct_ptr.contents.vk_code
                
                # Преобразуем виртуальный код клавиши в символ
                char = self._vk_to_char(vk_code)
                
                if char:
                    # Логируем символ (для Фазы 0)
                    logger.debug(f"Нажата клавиша: '{char}' (VK={vk_code})")
                    
                    # Вызываем пользовательский callback
                    try:
                        self.callback(char)
                    except Exception as e:
                        logger.error(f"Ошибка в callback хука: {e}", exc_info=True)
        
        # Пропускаем событие дальше по цепочке (не блокируем)
        return self.user32.CallNextHookEx(self.hook_handle, n_code, w_param, l_param)
    
    def _vk_to_char(self, vk_code: int) -> Optional[str]:
        """
        Преобразует виртуальный код клавиши в символ.
        
        Учитывает текущую раскладку клавиатуры (RU/EN).
        Для непечатных клавиш (Ctrl, Alt, Shift и т.д.) возвращает None.
        """
        # Диапазон печатных клавиш (буква, цифра, символ)
        # VK_A-Z: 65-90, VK_0-9: 48-57, другие символы
        
        # Простые случаи - буквы и цифры
        if 65 <= vk_code <= 90:  # A-Z
            # GetKeyState для проверки Shift
            shift_pressed = self.user32.GetKeyState(0x10) < 0
            
            # Получаем текущую раскладку
            hkl = self.user32.GetKeyboardLayout(0)
            
            # Буфер для символа
            buf = ctypes.create_unicode_buffer(2)
            
            # MapVirtualKeyEx переводит VK в scan code, затем в символ
            scan_code = self.user32.MapVirtualKeyExW(vk_code, 0, hkl)
            
            # Используем ToUnicodeEx для учёта раскладки и модификаторов
            state = (ctypes.c_byte * 256)()
            # Проверяем CapsLock
            if self.user32.GetKeyState(0x14) & 1:
                state[0x14] = 0x01
            
            # Shift
            if shift_pressed:
                state[0x10] = 0x80
            
            result = self.user32.ToUnicodeEx(
                vk_code, scan_code, state, buf, len(buf), 0, hkl
            )
            
            if result > 0:
                return buf.value
            elif result == 0:
                # Мёртвая клавиша (например, ^ или `), ждём следующую
                return None
            else:
                # Не печатная комбинация
                return None
        
        elif 48 <= vk_code <= 57:  # 0-9
            # Цифры могут быть сдвинуты Shift (!@#$...)
            shift_pressed = self.user32.GetKeyState(0x10) < 0
            
            hkl = self.user32.GetKeyboardLayout(0)
            buf = ctypes.create_unicode_buffer(2)
            scan_code = self.user32.MapVirtualKeyExW(vk_code, 0, hkl)
            state = (ctypes.c_byte * 256)()
            
            if shift_pressed:
                state[0x10] = 0x80
            
            result = self.user32.ToUnicodeEx(vk_code, scan_code, state, buf, len(buf), 0, hkl)
            if result > 0:
                return buf.value
            # Fallback к базовой цифре
            return chr(vk_code)
        
        # Пробел
        elif vk_code == 0x20:
            return ' '
        
        # Остальные печатные символы (.,;:/?[] и т.д.)
        else:
            hkl = self.user32.GetKeyboardLayout(0)
            buf = ctypes.create_unicode_buffer(2)
            scan_code = self.user32.MapVirtualKeyExW(vk_code, 0, hkl)
            state = (ctypes.c_byte * 256)()
            
            shift_pressed = self.user32.GetKeyState(0x10) < 0
            if shift_pressed:
                state[0x10] = 0x80
            
            result = self.user32.ToUnicodeEx(vk_code, scan_code, state, buf, len(buf), 0, hkl)
            if result > 0:
                return buf.value
        
        return None
    
    def start(self):
        """Запускает хук в отдельном потоке."""
        if self._running:
            logger.warning("Хук уже запущен")
            return
        
        self._running = True
        
        # Создаём функцию-обработчик
        # ВАЖНО: сохраняем ссылку на hook_proc в атрибуте экземпляра,
        # чтобы она не была уничтожена сборщиком мусора
        self._hook_proc = HOOKPROC(self._low_level_handler)
        
        # Для WH_KEYBOARD_LL параметр hInstance ДОЛЖЕН быть NULL (0)
        # Согласно документации Microsoft: "This parameter must be NULL if the dwThreadId parameter is zero"
        # и для low-level хуков используется 0
        h_instance = None  # ctypes интерпретирует это как NULL
        
        logger.debug(f"Установка хука с hInstance={h_instance}")
        
        # Устанавливаем хук
        self.hook_handle = self.user32.SetWindowsHookExA(
            WH_KEYBOARD_LL,
            self._hook_proc,
            h_instance,
        # Создаём функцию-обработчик (должна жить пока хук активен)
        self._hook_proc = HOOKPROC(self._low_level_handler)
        
        # Устанавливаем хук
        # HINSTANCE = NULL (0) для WH_KEYBOARD_LL
        self.hook_handle = self.user32.SetWindowsHookExA(
            WH_KEYBOARD_LL,
            self._hook_proc,
            self.kernel32.GetModuleHandleW(None),  # HINSTANCE текущего модуля
            0  # 0 = глобальный хук для всех потоков
        )
        
        if not self.hook_handle:
            error_code = self.kernel32.GetLastError()
            # Снимает хук на всякий случай
            self._running = False
            raise RuntimeError(f"Не удалось установить хук. Код ошибки: {error_code}")
        
        logger.info("Хук клавиатуры успешно установлен")
        
        # Запускаем цикл сообщений в отдельном потоке
        self._thread = threading.Thread(target=self._message_loop, daemon=True)
        self._thread.start()
    
    def _message_loop(self):
        """Цикл обработки сообщений Windows для хука."""
        msg = wintypes.MSG()
        while self._running:
            # Получаем сообщение из очереди
            ret = self.user32.GetMessageW(ctypes.byref(msg), None, 0, 0)
            if ret == -1:
                logger.error("GetMessage вернул -1")
                break
            elif ret == 0:
                # Сообщение WM_QUIT
                break
            
            self.user32.TranslateMessage(ctypes.byref(msg))
            self.user32.DispatchMessageW(ctypes.byref(msg))
    
    def stop(self):
        """Останавливает хук и освобождает ресурсы."""
        if not self._running:
            return
        
        self._running = False
        
        # Снимаем хук
        if self.hook_handle:
            self.user32.UnhookWindowsHookEx(self.hook_handle)
            self.hook_handle = None
            logger.info("Хук клавиатуры снят")
        
        # Ждём завершения потока
        if self._thread and self._thread.is_alive():
            # Посылаем WM_QUIT в поток хука
            self.user32.PostThreadMessageW(
                self._thread.ident, 0x0012, 0, 0
            )  # WM_QUIT = 0x0012
            self._thread.join(timeout=2.0)


# Обёртки для совместимости (если нужно)
def install_hook(callback: Callable[[str], None]) -> KeyboardHook:
    """Установить глобальный хук клавиатуры."""
    hook = KeyboardHook(callback)
    hook.start()
    return hook


def uninstall_hook(hook: KeyboardHook):
    """Снять хук клавиатуры."""
    hook.stop()
