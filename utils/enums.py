"""
Moduł zawierający enumeracje używane w symulacji.
"""
from enum import Enum


class Season(Enum):
    """Enumeracja reprezentująca pory roku w symulacji."""
    SPRING = 1
    SUMMER = 2
    AUTUMN = 3
    WINTER = 4