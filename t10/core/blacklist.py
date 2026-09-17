# TODO: Реализовать чёрный список приложений (где коррекция отключена)

class Blacklist:
    """Управление списком процессов, где коррекция отключена"""
    
    def __init__(self, apps: list = None):
        self.apps = set(apps) if apps else set()
    
    def add(self, app_name: str):
        """Добавить приложение в чёрный список"""
        pass
    
    def remove(self, app_name: str):
        """Удалить приложение из чёрного списка"""
        pass
    
    def contains(self, app_name: str) -> bool:
        """Проверить, есть ли приложение в чёрном списке"""
        pass
    
    def get_current_process_name() -> str:
        """Получить имя текущего активного процесса"""
        pass
