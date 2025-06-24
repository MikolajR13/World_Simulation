"""
Moduł definiujący klasę Field (Pole) dla symulacji.
"""
from utils.enums import Season


class Field:
    """
    Klasa reprezentująca pojedyncze pole na mapie z określonymi parametrami.
    """

    def __init__(self, terrain_difficulty=50, danger=50,
                 water_availability=50, food_availability=50,
                 can_build=True):
        """
        Inicjalizuje pole z domyślnymi lub podanymi parametrami.

        Args:
            terrain_difficulty (int): Trudność terenu (1-100)
            danger (int): Niebezpieczeństwo (1-100)
            water_availability (int): Dostępność wody (1-100)
            food_availability (int): Dostępność jedzenia (1-100)
            can_build (bool): Czy można budować na tym polu
        """
        self.terrain_difficulty = terrain_difficulty
        self.danger = danger
        self.water_availability = water_availability
        self.food_availability = food_availability
        self.can_build = can_build

    def update_resources(self, season: Season, weather_condition: int, food_modifier: float = 1.0):
        """
        Aktualizuje zasoby pola w zależności od sezonu i pogody.

        Args:
            season (Season): Aktualny sezon
            weather_condition (int): Warunki pogodowe (1-100)
        """
        # Modyfikacja dostępności wody w zależności od sezonu
        if season == Season.SPRING:
            self.water_availability = min(100, self.water_availability + 5)
        elif season == Season.SUMMER:
            self.water_availability = max(0, self.water_availability - 3)
        elif season == Season.AUTUMN:
            self.water_availability = min(100, self.water_availability + 2)
        elif season == Season.WINTER:
            # Zimą woda jest mniej dostępna (np. zamarznięta)
            self.water_availability = max(0, self.water_availability - 5)

        # Modyfikacja dostępności jedzenia w zależności od sezonu
        base_food_increase = 0
        if season == Season.SPRING:
            base_food_increase = 3
        elif season == Season.SUMMER:
            base_food_increase = 7
        elif season == Season.AUTUMN:
            base_food_increase = 1
        elif season == Season.WINTER:
            base_food_increase = -7 # Zimą jedzenie jest trudniejsze do znalezienia

        # Zastosowanie globalnego modyfikatora jedzenia
        # Modyfikator wpływa na przyrost/spadek, a nie na absolutną wartość
        effective_food_change = base_food_increase * food_modifier
        self.food_availability = max(0, min(100, self.food_availability + effective_food_change))

        # Wpływ pogody na dostępność zasobów
        # Ekstremalne warunki pogodowe zmniejszają dostępność
        if weather_condition > 80:
            self.water_availability = max(0, self.water_availability - 10)
            self.food_availability = max(0, self.food_availability - 10)
            self.danger = min(100, self.danger + 15)
        elif weather_condition < 20:  # Idealne warunki
            self.water_availability = min(100, self.water_availability + 5)
            self.food_availability = min(100, self.food_availability + 5)
            self.danger = max(0, self.danger - 5)

        # Naturalna regeneracja zasobów (w granicach)
        self.water_availability = min(100, self.water_availability + 1)
        self.food_availability = min(100, self.food_availability + (1 * food_modifier))
        self.food_availability = max(0, min(100, self.food_availability))

    def determine_impact_on_agent(self, agent):
        """
        Określa, jak parametry pola wpływają na agenta.

        Args:
            agent: Agent, na którego wpływa pole
        """
        # Wpływ niebezpieczeństwa na agenta
        if self.danger > 60:
            agent.health = max(0, agent.health - 2)
            agent.mortality = min(100, agent.mortality + 3)
        elif self.danger < 30:
            agent.health = min(100, agent.health + 1)
            agent.mortality = max(0, agent.mortality - 1)

        # Wpływ trudności terenu na wytrzymałość agenta
        if self.terrain_difficulty > 70:
            agent.endurance = max(0, agent.endurance - 3)

        # Wpływ dostępności zasobów na agenta
        if self.water_availability < 30:
            agent.thirst = min(100, agent.thirst + 3)

        if self.food_availability < 30:
            agent.hunger = min(100, agent.hunger + 3)

    def improve_parameters(self, water_change: int, food_change: int,
                           danger_change: int):
        """
        Modyfikuje parametry pola.

        Args:
            water_change (int): Zmiana dostępności wody
            food_change (int): Zmiana dostępności jedzenia
            danger_change (int): Zmiana poziomu niebezpieczeństwa
        """
        self.water_availability = max(0, min(100, self.water_availability + water_change))
        self.food_availability = max(0, min(100, self.food_availability + food_change))
        self.danger = max(0, min(100, self.danger + danger_change))