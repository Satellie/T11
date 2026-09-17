# TODO: Реализовать пользовательский словарь (whitelist слов, которые не нужно исправлять)
# Файл data/user_dictionary.txt растёт по мере использования

class Whitelist:
    """Управление пользовательским словарём исключений"""
    
    def __init__(self, filepath: str = "data/user_dictionary.txt"):
        self.filepath = filepath
        self.words = set()
        self._load()
    
    def _load(self):
        """Загрузить слова из файла"""
        pass
    
    def add(self, word: str):
        """Добавить слово в whitelist"""
        pass
    
    def contains(self, word: str) -> bool:
        """Проверить, есть ли слово в whitelist"""
        pass
    
    def save(self):
        """Сохранить whitelist в файл"""
        pass
