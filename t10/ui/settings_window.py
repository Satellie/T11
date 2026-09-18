"""
ui/settings_window.py - Окно настроек приложения на tkinter.
Вкладки: Общие, Чёрный список приложений, Словарь пользователя, Статистика.
"""
import logging
import tkinter as tk
from tkinter import ttk, simpledialog, messagebox
from typing import Optional, Callable, List

logger = logging.getLogger(__name__)


class SettingsWindow:
    """
    Окно настроек приложения с вкладками.
    Позволяет управлять хоткеями, чёрным списком, словарём и просматривать статистику.
    """

    def __init__(self,
                 get_settings: Callable[[], dict],
                 save_settings: Callable[[dict], None],
                 get_blacklist: Callable[[], List[str]],
                 add_to_blacklist: Callable[[str], None],
                 remove_from_blacklist: Callable[[str], None],
                 get_whitelist: Callable[[], List[str]],
                 add_to_whitelist: Callable[[str], None],
                 remove_from_whitelist: Callable[[str], None],
                 get_stats: Callable[[], dict]):
        
        self.get_settings = get_settings
        self.save_settings = save_settings
        self.get_blacklist = get_blacklist
        self.add_to_blacklist = add_to_blacklist
        self.remove_from_blacklist = remove_from_blacklist
        self.get_whitelist = get_whitelist
        self.add_to_whitelist = add_to_whitelist
        self.remove_from_whitelist = remove_from_whitelist
        self.get_stats = get_stats
        
        self.window: Optional[tk.Tk] = None
        self.notebook: Optional[ttk.Notebook] = None

    def _create_general_tab(self, parent) -> ttk.Frame:
        """Вкладка 'Общие': хоткеи, язык, уведомления, облачный фоллбэк."""
        frame = ttk.Frame(parent, padding="10")
        
        # Хоткей отката
        lbl_hotkey = ttk.Label(frame, text="Хоткей отката (Ctrl+Shift+Z):")
        lbl_hotkey.grid(row=0, column=0, sticky=tk.W, pady=5)
        
        settings = self.get_settings()
        hotkey_var = tk.StringVar(value=settings.get('undo_hotkey', 'Ctrl+Shift+Z'))
        
        def on_hotkey_change(*args):
            new_val = hotkey_var.get()
            settings['undo_hotkey'] = new_val
            self.save_settings(settings)
            logger.info(f"Хоткей отката изменён на: {new_val}")
        
        hotkey_var.trace_add("write", on_hotkey_change)
        entry_hotkey = ttk.Entry(frame, textvariable=hotkey_var, width=30)
        entry_hotkey.grid(row=0, column=1, sticky=tk.W, pady=5)
        
        # Приоритет языка
        lbl_lang = ttk.Label(frame, text="Приоритетный язык:")
        lbl_lang.grid(row=1, column=0, sticky=tk.W, pady=5)
        
        lang_var = tk.StringVar(value=settings.get('priority_language', 'ru'))
        
        def on_lang_change(*args):
            new_val = lang_var.get()
            settings['priority_language'] = new_val
            self.save_settings(settings)
            logger.info(f"Приоритетный язык изменён на: {new_val}")
        
        lang_var.trace_add("write", on_lang_change)
        combo_lang = ttk.Combobox(frame, textvariable=lang_var, values=['ru', 'en'], state='readonly', width=28)
        combo_lang.grid(row=1, column=1, sticky=tk.W, pady=5)
        
        # Уведомления
        notif_var = tk.BooleanVar(value=settings.get('notifications_enabled', True))
        
        def on_notif_change(*args):
            new_val = notif_var.get()
            settings['notifications_enabled'] = new_val
            self.save_settings(settings)
            logger.info(f"Уведомления {'включены' if new_val else 'выключены'}")
        
        notif_var.trace_add("write", on_notif_change)
        chk_notif = ttk.Checkbutton(frame, text="Включить уведомления об исправлениях", variable=notif_var)
        chk_notif.grid(row=2, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        # Облачный фоллбэк (Yandex Speller)
        cloud_var = tk.BooleanVar(value=settings.get('use_cloud_fallback', False))
        
        def on_cloud_change(*args):
            new_val = cloud_var.get()
            settings['use_cloud_fallback'] = new_val
            self.save_settings(settings)
            if new_val:
                logger.warning("Облачный фоллбэк ВКЛЮЧЕН: текст отправляется в Яндекс.")
            else:
                logger.info("Облачный фоллбэк ВЫКЛЮЧЕН.")
        
        cloud_var.trace_add("write", on_cloud_change)
        chk_cloud = ttk.Checkbutton(frame, 
                                    text="Разрешить облачную проверку (отправляет текст в Яндекс)", 
                                    variable=cloud_var)
        chk_cloud.grid(row=3, column=0, columnspan=2, sticky=tk.W, pady=5)
        
        lbl_cloud_warning = ttk.Label(frame, 
                                      text="(Внимание: это снижает приватность, но улучшает качество исправлений)", 
                                      font=('TkDefaultFont', 8, 'italic'), foreground='gray')
        lbl_cloud_warning.grid(row=4, column=0, columnspan=2, sticky=tk.W, padx=20, pady=(0, 10))
        
        return frame

    def _create_blacklist_tab(self, parent) -> ttk.Frame:
        """Вкладка 'Чёрный список приложений': список .exe, добавить/удалить."""
        frame = ttk.Frame(parent, padding="10")
        
        # Список
        listbox_frame = ttk.LabelFrame(frame, text="Приложения, где коррекция отключена")
        listbox_frame.grid(row=0, column=0, columnspan=2, sticky=tk.NSEW, pady=5)
        
        listbox = tk.Listbox(listbox_frame, width=40, height=15)
        scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=listbox.yview)
        listbox.configure(yscrollcommand=scrollbar.set)
        
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        def refresh_list():
            listbox.delete(0, tk.END)
            for app in sorted(self.get_blacklist()):
                listbox.insert(tk.END, app)
        
        refresh_list()
        
        # Кнопки
        def on_add():
            app_name = simpledialog.askstring("Добавить приложение", 
                                              "Введите имя процесса (например, code.exe):")
            if app_name:
                app_name = app_name.strip().lower()
                if not app_name.endswith('.exe'):
                    app_name += '.exe'
                self.add_to_blacklist(app_name)
                refresh_list()
                logger.info(f"Добавлено в чёрный список: {app_name}")
        
        def on_remove():
            selection = listbox.curselection()
            if selection:
                app_name = listbox.get(selection[0])
                self.remove_from_blacklist(app_name)
                refresh_list()
                logger.info(f"Удалено из чёрного списка: {app_name}")
            else:
                messagebox.showwarning("Предупреждение", "Выберите приложение для удаления")
        
        btn_add = ttk.Button(frame, text="Добавить", command=on_add)
        btn_add.grid(row=1, column=0, sticky=tk.W, pady=5)
        
        btn_remove = ttk.Button(frame, text="Удалить", command=on_remove)
        btn_remove.grid(row=1, column=1, sticky=tk.E, pady=5)
        
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        
        return frame

    def _create_whitelist_tab(self, parent) -> ttk.Frame:
        """Вкладка 'Словарь пользователя': список слов, добавить/удалить."""
        frame = ttk.Frame(parent, padding="10")
        
        # Список
        listbox_frame = ttk.LabelFrame(frame, text="Слова, которые не нужно исправлять")
        listbox_frame.grid(row=0, column=0, columnspan=2, sticky=tk.NSEW, pady=5)
        
        listbox = tk.Listbox(listbox_frame, width=40, height=15)
        scrollbar = ttk.Scrollbar(listbox_frame, orient=tk.VERTICAL, command=listbox.yview)
        listbox.configure(yscrollcommand=scrollbar.set)
        
        listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        def refresh_list():
            listbox.delete(0, tk.END)
            for word in sorted(self.get_whitelist()):
                listbox.insert(tk.END, word)
        
        refresh_list()
        
        # Кнопки
        def on_add():
            word = simpledialog.askstring("Добавить слово", 
                                          "Введите слово, которое не нужно исправлять:")
            if word:
                word = word.strip()
                self.add_to_whitelist(word)
                refresh_list()
                logger.info(f"Добавлено в словарь: {word}")
        
        def on_remove():
            selection = listbox.curselection()
            if selection:
                word = listbox.get(selection[0])
                self.remove_from_whitelist(word)
                refresh_list()
                logger.info(f"Удалено из словаря: {word}")
            else:
                messagebox.showwarning("Предупреждение", "Выберите слово для удаления")
        
        btn_add = ttk.Button(frame, text="Добавить", command=on_add)
        btn_add.grid(row=1, column=0, sticky=tk.W, pady=5)
        
        btn_remove = ttk.Button(frame, text="Удалить", command=on_remove)
        btn_remove.grid(row=1, column=1, sticky=tk.E, pady=5)
        
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)
        
        return frame

    def _create_stats_tab(self, parent) -> ttk.Frame:
        """Вкладка 'Статистика': текстовые цифры исправлений."""
        frame = ttk.Frame(parent, padding="10")
        
        stats = self.get_stats()
        
        lbl_today = ttk.Label(frame, text=f"Исправлений сегодня: {stats.get('today', 0)}", font=('TkDefaultFont', 12, 'bold'))
        lbl_today.grid(row=0, column=0, sticky=tk.W, pady=10)
        
        lbl_week = ttk.Label(frame, text=f"Исправлений за неделю: {stats.get('week', 0)}", font=('TkDefaultFont', 12))
        lbl_week.grid(row=1, column=0, sticky=tk.W, pady=5)
        
        lbl_total = ttk.Label(frame, text=f"Всего исправлений: {stats.get('total', 0)}", font=('TkDefaultFont', 12))
        lbl_total.grid(row=2, column=0, sticky=tk.W, pady=5)
        
        lbl_info = ttk.Label(frame, text="(Статистика обновляется при закрытии этого окна)", font=('TkDefaultFont', 9, 'italic'), foreground='gray')
        lbl_info.grid(row=3, column=0, sticky=tk.W, pady=20)
        
        return frame

    def show(self):
        """Показать окно настроек (модально)."""
        if self.window and self.window.winfo_exists():
            self.window.lift()
            self.window.focus_force()
            return
        
        self.window = tk.Tk()
        self.window.title("t10 - Настройки")
        self.window.geometry("500x450")
        self.window.resizable(True, True)
        
        # Вкладки
        self.notebook = ttk.Notebook(self.window)
        self.notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        tab_general = self._create_general_tab(self.notebook)
        tab_blacklist = self._create_blacklist_tab(self.notebook)
        tab_whitelist = self._create_whitelist_tab(self.notebook)
        tab_stats = self._create_stats_tab(self.notebook)
        
        self.notebook.add(tab_general, text="Общие")
        self.notebook.add(tab_blacklist, text="Чёрный список")
        self.notebook.add(tab_whitelist, text="Словарь")
        self.notebook.add(tab_stats, text="Статистика")
        
        # Закрытие окна
        def on_close():
            # Обновляем статистику перед закрытием
            self.window.destroy()
            self.window = None
            logger.info("Окно настроек закрыто")
        
        self.window.protocol("WM_DELETE_WINDOW", on_close)
        
        # Центрирование окна
        self.window.update_idletasks()
        x = (self.window.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.window.winfo_screenheight() // 2) - (450 // 2)
        self.window.geometry(f'+{x}+{y}')
        
        logger.info("Окно настроек открыто")
        self.window.mainloop()

    def hide(self):
        """Скрыть окно настроек."""
        if self.window and self.window.winfo_exists():
            self.window.withdraw()
