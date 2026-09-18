# TODO: Реализовать эмуляцию Backspace + ввода текста (SendInput)
# Используется для замены исправленного слова в активном приложении

import ctypes
import ctypes.wintypes
import time

# Константы SendInput
INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004
VK_BACK = 0x08

# Структуры Windows API
class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", ctypes.wintypes.WORD),
        ("wScan", ctypes.wintypes.WORD),
        ("dwFlags", ctypes.wintypes.DWORD),
        ("time", ctypes.wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.wintypes.ULONG))
    ]

class INPUT(ctypes.Structure):
    class _INPUT(ctypes.Union):
        _fields_ = [("ki", KEYBDINPUT)]
    _anonymous_ = ["_input"]
    _fields_ = [
        ("type", ctypes.wintypes.DWORD),
        ("_input", _INPUT)
    ]


def send_backspace(count: int):
    """
    Отправить нажатия Backspace через SendInput.
    Каждый Backspace — это нажатие (keydown) и отпускание (keyup).
    """
    user32 = ctypes.windll.user32
    
    inputs = []
    for _ in range(count):
        # Keydown
        key_down = INPUT()
        key_down.type = INPUT_KEYBOARD
        key_down.ki.wVk = VK_BACK
        key_down.ki.wScan = 0
        key_down.ki.dwFlags = 0
        key_down.ki.time = 0
        key_down.ki.dwExtraInfo = None
        inputs.append(key_down)
        
        # Keyup
        key_up = INPUT()
        key_up.type = INPUT_KEYBOARD
        key_up.ki.wVk = VK_BACK
        key_up.ki.wScan = 0
        key_up.ki.dwFlags = KEYEVENTF_KEYUP
        key_up.ki.time = 0
        key_up.ki.dwExtraInfo = None
        inputs.append(key_up)
    
    if inputs:
        # Отправляем пакет нажатий
        input_array = (INPUT * len(inputs))(*inputs)
        user32.SendInput(len(inputs), input_array, ctypes.sizeof(INPUT))
        # Небольшая задержка для гарантии обработки
        time.sleep(0.01)


def send_text(text: str):
    """
    Отправить текст посимвольно через SendInput с флагом KEYEVENTF_UNICODE.
    Это позволяет печатать любые символы (включая русские) независимо от раскладки.
    """
    user32 = ctypes.windll.user32
    
    inputs = []
    for char in text:
        # Получаем Unicode код символа
        code = ord(char)
        
        # Keydown для Unicode символа
        key_down = INPUT()
        key_down.type = INPUT_KEYBOARD
        key_down.ki.wVk = 0  # Для Unicode wVk должен быть 0
        key_down.ki.wScan = code
        key_down.ki.dwFlags = KEYEVENTF_UNICODE
        key_down.ki.time = 0
        key_down.ki.dwExtraInfo = None
        inputs.append(key_down)
        
        # Keyup для Unicode символа
        key_up = INPUT()
        key_up.type = INPUT_KEYBOARD
        key_up.ki.wVk = 0
        key_up.ki.wScan = code
        key_up.ki.dwFlags = KEYEVENTF_UNICODE | KEYEVENTF_KEYUP
        key_up.ki.time = 0
        key_up.ki.dwExtraInfo = None
        inputs.append(key_up)
    
    if inputs:
        input_array = (INPUT * len(inputs))(*inputs)
        user32.SendInput(len(inputs), input_array, ctypes.sizeof(INPUT))
        # Небольшая задержка для гарантии обработки
        time.sleep(0.01)


def replace_word(old_len: int, new_word: str):
    """
    Заменить слово: отправить old_len нажатий Backspace, затем ввести new_word.
    Это основная функция для тихой автокоррекции.
    """
    if old_len <= 0:
        return
    
    # Сначала удаляем старое слово
    send_backspace(old_len)
    
    # Затем вводим исправленное слово
    send_text(new_word)
