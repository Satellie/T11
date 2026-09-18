"""
Менеджер отката исправлений (Undo).
Регистрирует глобальный хоткей и выполняет обратную замену слова.
"""
import threading
import time
from typing import Optional, Callable, Any
from pathlib import Path

# Импорты Windows API только при запуске на Windows
try:
    import ctypes
    from ctypes import wintypes
    import win32gui
    import win32process
    import win32con
    WINDOWS_AVAILABLE = True
except ImportError:
    WINDOWS_AVAILABLE = False

from .history import CorrectionHistory, CorrectionRecord
from .sender import replace_word


class UndoManager:
    """Управление откатом последних исправлений через глобальный хоткей."""
    
    DEFAULT_HOTKEY = "Ctrl+Shift+Z"
    
    def __init__(self, history: CorrectionHistory, hotkey: str = DEFAULT_HOTKEY):
        self.history = history
        self.hotkey = hotkey  # Формат: "Ctrl+Shift+Z"
        self.hotkey_id = None
        self.callback_thread: Optional[threading.Thread] = None
        self.running = False
        
        # Парсинг хоткея
        self.modifiers, self.vk_code = self._parse_hotkey(hotkey)
        
        if WINDOWS_AVAILABLE:
            self.user32 = ctypes.windll.user32
            self._register_hotkey()

    def _parse_hotkey(self, hotkey_str: str) -> tuple:
        """Парсинг строки хоткея в модификаторы и VK-код."""
        parts = hotkey_str.upper().replace(" ", "").split("+")
        vk_name = parts[-1]
        mods = parts[:-1]
        
        # Маппинг модификаторов (числовые значения из win32con)
        # MOD_CONTROL=2, MOD_SHIFT=4, MOD_ALT=1, MOD_WIN=8
        mod_map = {
            "CTRL": 2,
            "SHIFT": 4,
            "ALT": 1,
            "WIN": 8
        }
        
        mod_flags = 0
        for m in mods:
            mod_flags |= mod_map.get(m, 0)
        
        # Маппинг виртуальных кодов (VK_коды из win32con)
        vk_map = {
            "A": 0x41, "B": 0x42, "C": 0x43, "D": 0x44, "E": 0x45,
            "F": 0x46, "G": 0x47, "H": 0x48, "I": 0x49, "J": 0x4A,
            "K": 0x4B, "L": 0x4C, "M": 0x4D, "N": 0x4E, "O": 0x4F,
            "P": 0x50, "Q": 0x51, "R": 0x52, "S": 0x53, "T": 0x54,
            "U": 0x55, "V": 0x56, "W": 0x57, "X": 0x58, "Y": 0x59,
            "Z": 0x5A
        }
        
        return mod_flags, vk_map.get(vk_name, 0x5A)  # По умолчанию Z

    def _register_hotkey(self):
        """Регистрация глобального хоткея через Windows API."""
        if not WINDOWS_AVAILABLE:
            return
            
        # Создаем невидимое окно для получения сообщений о хоткеях
        wc = win32gui.WNDCLASS()
        wc.hInstance = win32gui.GetModuleHandle(None)
        wc.lpszClassName = "t10UndoHotkey"
        wc.lpfnWndProc = self._wnd_proc
        
        class_atom = win32gui.RegisterClass(wc)
        self.hwnd = win32gui.CreateWindowEx(
            0, class_atom, "t10 Undo Hotkey",
            0, 0, 0, 0, 0, 0, wc.hInstance, None
        )
        
        # Регистрация хоткея
        success = self.user32.RegisterHotKey(
            self.hwnd,
            1,  # ID хоткея
            self.modifiers,
            self.vk_code
        )
        
        if not success:
            print(f"[WARNING] Не удалось зарегистрировать хоткей {self.hotkey}")
        else:
            print(f"[INFO] Хоткей отката зарегистрирован: {self.hotkey}")
            
        # Запуск цикла обработки сообщений
        self.running = True
        self.callback_thread = threading.Thread(target=self._message_loop, daemon=True)
        self.callback_thread.start()

    def _wnd_proc(self, hwnd, msg, wParam, lParam):
        """Обработчик сообщений окна (для хоткеев)."""
        if msg == win32con.WM_HOTKEY and wParam == 1:
            self._on_hotkey_pressed()
        return win32gui.DefWindowProc(hwnd, msg, wParam, lParam)

    def _message_loop(self):
        """Цикл обработки сообщений Windows."""
        import pythoncom
        pythoncom.CoInitialize()
        
        while self.running:
            try:
                import win32api
                win32gui.PeekMessage(None, 0, 0, win32con.PM_REMOVE)
                time.sleep(0.1)
            except Exception as e:
                if self.running:
                    print(f"[ERROR] Ошибка в цикле сообщений undo: {e}")
                break
                
        pythoncom.CoUninitialize()

    def _on_hotkey_pressed(self):
        """Обработка нажатия хоткея - выполнение отката."""
        try:
            # Получаем текущее активное окно
            current_hwnd = win32gui.GetForegroundWindow()
            _, current_pid = win32process.GetWindowThreadProcessId(current_hwnd)
            current_title = win32gui.GetWindowText(current_hwnd)
            
            # Получаем имя процесса
            import psutil
            try:
                process = psutil.Process(current_pid)
                current_process_name = process.name()
            except Exception:
                current_process_name = ""
            
            # Получаем последнюю запись из истории
            last_record = self.history.get_last()
            
            if last_record is None:
                print("[INFO] Нечего отменять - история пуста")
                return
            
            # Проверяем, что мы всё ещё в том же окне
            if (last_record.process_name != current_process_name or 
                last_record.window_title != current_title):
                print("[INFO] Отмена отменена: фокус сменился с момента исправления")
                # Здесь можно отправить уведомление через tray
                return
            
            # Выполняем обратную замену
            print(f"[UNDO] Отмена исправления: '{last_record.corrected}' → '{last_record.original}'")
            
            # Вычисляем длину исправленного слова и заменяем на оригинал
            replace_word(len(last_record.corrected), last_record.original)
            
            # Помечаем запись как отмененную
            self.history.mark_undone(last_record)
            
        except Exception as e:
            print(f"[ERROR] Ошибка при откате исправления: {e}")

    def stop(self):
        """Остановка менеджера отката."""
        self.running = False
        if self.hotkey_id is not None and WINDOWS_AVAILABLE:
            self.user32.UnregisterHotKey(self.hwnd, 1)
        if self.callback_thread:
            self.callback_thread.join(timeout=1.0)

    def set_hotkey(self, new_hotkey: str):
        """Изменение хоткея на лету."""
        self.stop()
        self.hotkey = new_hotkey
        self.modifiers, self.vk_code = self._parse_hotkey(new_hotkey)
        if WINDOWS_AVAILABLE:
            self._register_hotkey()
