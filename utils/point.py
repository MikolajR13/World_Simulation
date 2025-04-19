"""
Moduł definiujący strukturę punktu dla określania pozycji na mapie.
"""
from dataclasses import dataclass


@dataclass
class Point:
    """Prosta struktura reprezentująca pozycję na mapie."""
    x: int
    y: int

    def __eq__(self, other):
        if not isinstance(other, Point):
            return False
        return self.x == other.x and self.y == other.y

    def __hash__(self):
        return hash((self.x, self.y))