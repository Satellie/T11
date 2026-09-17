# TODO: Определить схему настроек с помощью dataclass или pydantic
from dataclasses import dataclass
from typing import List, Optional


@dataclass
class SettingsSchema:
    """Схема настроек приложения t10"""
    # TODO: Добавить поля согласно settings.json
    # blacklist_apps: List[str]
    # hotkey_undo: str
    # enable_notifications: bool
    # language_priority: str
    # use_yandex_fallback: bool
    pass
