# TODO: Реализовать фильтры для игнорирования:
# URL, email, пути к файлам, числа, ники (@username), хэштеги (#tag),
# поля паролей, вставку из буфера обмена

def is_url(text: str) -> bool:
    """Проверить, является ли текст URL"""
    pass

def is_email(text: str) -> bool:
    """Проверить, является ли текст email"""
    pass

def is_file_path(text: str) -> bool:
    """Проверить, является ли текст путём к файлу"""
    pass

def is_number(text: str) -> bool:
    """Проверить, является ли текст числом"""
    pass

def is_username(text: str) -> bool:
    """Проверить, является ли текст ником (@username)"""
    pass

def is_hashtag(text: str) -> bool:
    """Проверить, является ли текст хэштегом (#tag)"""
    pass

def should_ignore(word: str, context: dict) -> bool:
    """Комплексная проверка: нужно ли игнорировать слово"""
    pass
