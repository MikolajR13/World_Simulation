"""
Moduł definiujący klasę Map (Mapa) dla symulacji.
"""
from typing import List, Optional
import numpy as np

from utils.point import Point
from models.field import Field


class Map:
    """
    Klasa reprezentująca mapę składającą się z pól.
    """

    def __init__(self, width: int, height: int):
        """
        Inicjalizuje mapę o podanej szerokości i wysokości.

        Args:
            width (int): Szerokość mapy (liczba pól w poziomie)
            height (int): Wysokość mapy (liczba pól w pionie)
        """
        self.width = width
        self.height = height
        self.fields = [[Field() for _ in range(width)] for _ in range(height)]

        # Inicjalizacja pól z losowymi wartościami
        self._initialize_fields()

    def _initialize_fields(self):
        """Inicjalizuje pola z losowymi wartościami parametrów."""
        for y in range(self.height):
            for x in range(self.width):
                # Losowe wartości dla parametrów pola
                terrain_difficulty = np.random.randint(20, 80)
                danger = np.random.randint(20, 80)
                water_availability = np.random.randint(20, 80)
                food_availability = np.random.randint(20, 80)
                can_build = np.random.random() > 0.3  # 70% pól pozwala na budowę

                self.fields[y][x] = Field(
                    terrain_difficulty=terrain_difficulty,
                    danger=danger,
                    water_availability=water_availability,
                    food_availability=food_availability,
                    can_build=can_build
                )

    def get_field(self, position: Point) -> Optional[Field]:
        """
        Zwraca pole na danej pozycji.

        Args:
            position (Point): Pozycja pola

        Returns:
            Optional[Field]: Pole na danej pozycji lub None, jeśli pozycja jest poza mapą
        """
        if 0 <= position.x < self.width and 0 <= position.y < self.height:
            return self.fields[position.y][position.x]
        return None

    def get_neighboring_fields(self, position: Point) -> List[tuple[Point, Field]]:
        """
        Zwraca listę sąsiednich pól wraz z ich pozycjami.

        Args:
            position (Point): Pozycja centralna

        Returns:
            List[tuple[Point, Field]]: Lista par (pozycja, pole) sąsiadujących z podaną pozycją
        """
        neighbors = []
        for dx in [-1, 0, 1]:
            for dy in [-1, 0, 1]:
                if dx == 0 and dy == 0:
                    continue
                new_pos = Point(position.x + dx, position.y + dy)
                field = self.get_field(new_pos)
                if field:
                    neighbors.append((new_pos, field))
        return neighbors

    def find_most_favorable_terrain(self, current_position: Point, radius: int) -> List[Point]:
        """
        Znajduje najkorzystniejsze tereny w określonym promieniu.

        Args:
            current_position (Point): Aktualna pozycja
            radius (int): Promień poszukiwań

        Returns:
            List[Point]: Lista pozycji najkorzystniejszych terenów
        """
        favorable_positions = []
        scores = {}

        # Sprawdzenie wszystkich pól w promieniu
        for y in range(max(0, current_position.y - radius),
                       min(self.height, current_position.y + radius + 1)):
            for x in range(max(0, current_position.x - radius),
                           min(self.width, current_position.x + radius + 1)):
                position = Point(x, y)
                if position == current_position:
                    continue

                field = self.get_field(position)
                if not field:
                    continue

                # Obliczenie oceny korzystności pola
                # Wyższa dostępność zasobów i niższe niebezpieczeństwo dają wyższą ocenę
                score = (field.water_availability + field.food_availability -
                         field.danger - field.terrain_difficulty)

                # Uwzględnienie odległości - bliższe pola są preferowane
                distance = max(abs(x - current_position.x), abs(y - current_position.y))
                score = score - distance * 5  # Kara za odległość

                scores[position] = score

        # Sortowanie pozycji według oceny
        sorted_positions = sorted(scores.keys(), key=lambda pos: scores[pos], reverse=True)

        # Zwrócenie najlepszych 3 pozycji (lub mniej, jeśli nie ma tylu)
        return sorted_positions[:3]

    def check_build_possibility(self, position: Point) -> bool:
        """
        Sprawdza, czy w danym miejscu można zbudować osadę.

        Args:
            position (Point): Pozycja do sprawdzenia

        Returns:
            bool: True jeśli można budować, False w przeciwnym razie
        """
        field = self.get_field(position)
        if not field:
            return False
        return field.can_build