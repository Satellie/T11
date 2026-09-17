# TODO: Реализовать состояние "текущее набираемое слово"
# Буферизация символов до разделителя (пробел, знак препинания, Enter)

class WordBuffer:
    def __init__(self):
        self.current_word = ""
    
    def add_char(self, char: str):
        """Добавить символ в текущее слово"""
        pass
    
    def clear(self):
        """Очистить буфер текущего слова"""
        pass
    
    def get_word(self) -> str:
        """Получить текущее слово"""
        return self.current_word
