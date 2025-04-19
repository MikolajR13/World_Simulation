"""
Moduł definiujący klasę Agent dla symulacji.
"""
from mesa import Agent as MesaAgent
import numpy as np
from typing import Optional, List

from utils.point import Point


class Agent(MesaAgent):
    """
    Klasa reprezentująca społeczeństwo/plemię w symulacji.
    """

    def __init__(self, unique_id: int, model, position: Point = None):
        """
        Inicjalizuje agenta z domyślnymi parametrami.

        Args:
            unique_id (int): Unikalny identyfikator agenta
            model: Model symulacji, do którego należy agent
            position (Point, optional): Początkowa pozycja agenta
        """
        super().__init__(unique_id, model)
        # Parametry życiowe
        self.health = 50
        self.age = 40  # Wartość średnia dla wieku
        self.population = 50
        self.fertility = 50
        self.mortality = 50

        # Parametry społeczne
        self.aggression = 50
        self.trust = 50
        self.resourcefulness = 50

        # Parametry zasobów
        self.hunger = 50
        self.thirst = 50
        self.water_supply = 50
        self.food_supply = 50

        # Parametry mobilności
        self.endurance = 50
        self.position = position

    def update_population(self):
        """Aktualizuje liczebność populacji."""
        new_population = self.population + (self.population * (self.fertility / 200)) - (
                    self.population * (self.mortality / 200))
        self.population = max(1, min(100, new_population))
        # Aktualizacja średniego wieku po zmianie liczebności
        self.update_age()

    """
    Dodatkowe metody modyfikujące do klasy Agent, których brakuje w oryginalnym kodzie
    """

    # Dodaj te metody do klasy Agent

    def update_age(self):
        """Aktualizuje średni wiek społeczeństwa."""
        # Stare jednostki + minimum dla nowych jednostek (przyrost)
        growth = max(0, (self.population * (self.fertility / 200)))
        if self.population + growth > 0:  # Zabezpieczenie przed dzieleniem przez 0
            self.age = ((self.age * self.population) + (1 * growth)) / (self.population + growth)
        # Naturalny przyrost wieku z czasem
        self.age += 0.1
        self.age = min(100, self.age)

    def collect_food_supply(self):
        """Zbiera zapasy jedzenia z aktualnego pola."""
        field = self.model.environment.map.get_field(self.position)
        if field:
            amount = min(10, field.food_availability) * (self.resourcefulness / 100)
            self.food_supply = min(100, self.food_supply + amount)
            field.food_availability = max(0, field.food_availability - amount)

    def collect_water_supply(self):
        """Zbiera zapasy wody z aktualnego pola."""
        field = self.model.environment.map.get_field(self.position)
        if field:
            amount = min(10, field.water_availability) * (self.resourcefulness / 100)
            self.water_supply = min(100, self.water_supply + amount)
            field.water_availability = max(0, field.water_availability - amount)

    def consume_food_supply(self):
        """Zużywa zapasy jedzenia proporcjonalnie do liczebności."""
        consumption = self.population / 200  # Bazowe zużycie
        self.food_supply = max(0, self.food_supply - consumption)

    def consume_water_supply(self):
        """Zużywa zapasy wody proporcjonalnie do liczebności."""
        consumption = self.population / 200  # Bazowe zużycie
        self.water_supply = max(0, self.water_supply - consumption)

    def migrate(self):
        """Przemieszcza agenta do korzystniejszego pola."""
        # Implementacja migracji
        if self.endurance < 25:
            return  # Za mało wytrzymałości na migrację

        best_terrains = self.model.environment.map.find_most_favorable_terrain(self.position, 3)
        if best_terrains:
            new_position = best_terrains[0]
            field = self.model.environment.map.get_field(self.position)
            migration_cost = 25 * (1 + field.terrain_difficulty / 100)

            if self.endurance >= migration_cost:
                self.endurance -= migration_cost
                self.position = new_position
                # Zwiększone zużycie zasobów podczas migracji
                self.consume_food_supply()
                self.consume_water_supply()
                self.last_migrated = self.model.current_period

    def check_interactions_with_agents(self):
        """Sprawdza możliwe interakcje z innymi agentami."""
        for agent in self.model.schedule.agents:
            if agent.unique_id != self.unique_id and agent.position == self.position:
                if self.aggression > 70 and agent.population < self.population:
                    self.attack_agent(agent)
                elif self.trust > 70 and agent.trust > 50:
                    self.merge_tribes(agent)

    def attack_agent(self, agent) -> bool:
        """Atakuje innego agenta. Zwraca True jeśli atak się powiódł."""
        # Implementacja ataku
        attack_success = (self.population / agent.population) * (self.aggression / 100)
        if np.random.random() < attack_success:
            # Atak się powiódł
            agent.health -= 20
            self.food_supply = min(100, self.food_supply + agent.food_supply * 0.5)
            self.water_supply = min(100, self.water_supply + agent.water_supply * 0.5)
            agent.food_supply *= 0.5
            agent.water_supply *= 0.5
            return True
        return False

    def merge_tribes(self, agent) -> bool:
        """Łączy plemiona z innym agentem. Zwraca True jeśli łączenie się powiodło."""
        # Implementacja łączenia plemion
        if np.random.random() < (self.trust + agent.trust) / 200:
            # Średnie wartości parametrów
            self.population += agent.population
            self.health = (self.health + agent.health) / 2
            self.age = (self.age * self.population + agent.age * agent.population) / (
                        self.population + agent.population)
            self.fertility = (self.fertility + agent.fertility) / 2
            self.mortality = (self.mortality + agent.mortality) / 2

            # Parametry społeczne - średnie ważone
            self.aggression = (self.aggression * self.population + agent.aggression * agent.population) / (
                        self.population + agent.population)
            self.trust = (self.trust * self.population + agent.trust * agent.population) / (
                        self.population + agent.population)
            self.resourcefulness = (
                                               self.resourcefulness * self.population + agent.resourcefulness * agent.population) / (
                                               self.population + agent.population)

            # Sumowanie zasobów
            self.food_supply = min(100, self.food_supply + agent.food_supply)
            self.water_supply = min(100, self.water_supply + agent.water_supply)

            # Usunięcie połączonego agenta
            self.model.schedule.remove(agent)
            return True
        return False

    def progress_to_next_period(self):
        """Aktualizuje parametry agenta po przejściu do następnego okresu."""
        # Naturalne zwiększenie wieku
        self.age = min(100, self.age + 0.1)


    def step(self):
        """Wykonuje krok agenta w symulacji."""
        self.update_hunger()
        self.update_thirst()
        self.update_health()
        self.update_population()

        # Zbieranie zasobów
        if self.hunger > 60:
            self.collect_food_supply()
        if self.thirst > 60:
            self.collect_water_supply()

        # Zużywanie zasobów
        self.consume_food_supply()
        self.consume_water_supply()

        # Decyzje strategiczne
        if self.food_supply < 30 or self.water_supply < 30:
            self.migrate()

        # Interakcje z innymi agentami
        self.check_interactions_with_agents()

        # Aktualizacja parametrów społecznych
        self.calculate_fertility()
        self.calculate_mortality()
        self.calculate_aggression()
        self.calculate_trust()
        self.calculate_resourcefulness()
        self.calculate_endurance()

        self.progress_to_next_period()

    def calculate_fertility(self):
        """Oblicza rozmnażalność na podstawie aktualnych parametrów."""
        base_fertility = self.fertility

        # Czynniki zwiększające rozmnażalność
        if self.health > 70:
            base_fertility += 5
        if self.hunger < 40:
            base_fertility += 3
        if self.thirst < 40:
            base_fertility += 3
        if 30 < self.population < 90:
            base_fertility += 2
        if self.age < 35:
            base_fertility += 4

        # Czynniki zmniejszające rozmnażalność
        if self.hunger > 60:
            base_fertility -= 5
        if self.thirst > 60:
            base_fertility -= 5
        if self.health < 40:
            base_fertility -= 5

        field = self.model.environment.map.get_field(self.position)
        if field and field.danger > 70:
            base_fertility -= 4

        if self.population > 90:
            base_fertility -= 6  # Przeludnienie
        if self.population < 30:
            base_fertility -= 6  # Zbyt mała populacja
        if self.age > 50:
            base_fertility -= 4  # Starsze społeczeństwo

        # Ograniczenie wartości do zakresu 1-100
        self.fertility = max(1, min(100, base_fertility))

    def calculate_mortality(self):
        """Oblicza śmiertelność na podstawie aktualnych parametrów."""
        base_mortality = self.mortality

        # Czynniki zwiększające śmiertelność
        if self.health < 40:
            base_mortality += 7
        if self.hunger > 80:
            base_mortality += 10
        if self.thirst > 80:
            base_mortality += 12
        if self.age > 45:
            # Zwiększa się proporcjonalnie do wieku
            base_mortality += (self.age - 45) / 5

        field = self.model.environment.map.get_field(self.position)
        if field and field.danger > 70:
            base_mortality += 8

        weather = self.model.environment.weather_condition
        if weather > 80:
            base_mortality += 6

        if self.aggression > 80:
            base_mortality += 3  # Konflikty wewnętrzne

        # Czynniki zmniejszające śmiertelność
        if self.health > 70:
            base_mortality -= 5
        if self.hunger < 40:
            base_mortality -= 3
        if self.thirst < 40:
            base_mortality -= 3

        if field and field.danger < 30:
            base_mortality -= 2

        if self.age < 35:
            base_mortality -= 4

        # Ograniczenie wartości do zakresu 1-100
        self.mortality = max(1, min(100, base_mortality))

    def calculate_aggression(self):
        """Oblicza agresję na podstawie aktualnych parametrów."""
        base_aggression = self.aggression

        # Czynniki zwiększające agresję
        if self.hunger > 70:
            base_aggression += 8
        if self.thirst > 70:
            base_aggression += 8
        if self.population > 80:
            base_aggression += 5
        if self.trust < 30:
            base_aggression += 7
        if self.resourcefulness < 30:
            base_aggression += 4
        if self.food_supply < 30:
            base_aggression += 6
        if self.water_supply < 30:
            base_aggression += 6

        # Czynniki zmniejszające agresję
        if self.trust > 70:
            base_aggression -= 7
        if self.food_supply > 80:
            base_aggression -= 5
        if self.water_supply > 80:
            base_aggression -= 5
        if self.population < 30:
            base_aggression -= 3
        if self.health < 30:
            base_aggression -= 4
        if self.resourcefulness > 70:
            base_aggression -= 6

        # Ograniczenie wartości do zakresu 1-100
        self.aggression = max(1, min(100, base_aggression))

    def calculate_trust(self):
        """Oblicza ufność na podstawie aktualnych parametrów."""
        base_trust = self.trust

        # Czynniki zwiększające ufność
        if self.food_supply > 80:
            base_trust += 6
        if self.water_supply > 80:
            base_trust += 6

        field = self.model.environment.map.get_field(self.position)
        if field and field.danger < 40:
            base_trust += 4

        if self.resourcefulness > 70:
            base_trust += 5
        if self.health > 70:
            base_trust += 4

        # Czynniki zmniejszające ufność
        if field and field.danger > 60:
            base_trust -= 6

        # Sprawdzenie, czy agent został wcześniej zaatakowany
        # Ta funkcja wymagałaby utrzymywania historii ataków

        if self.hunger > 70:
            base_trust -= 5
        if self.thirst > 70:
            base_trust -= 5
        if self.aggression > 70:
            base_trust -= 7

        weather = self.model.environment.weather_condition
        if weather > 80:
            base_trust -= 4

        # Ograniczenie wartości do zakresu 1-100
        self.trust = max(1, min(100, base_trust))

    def calculate_resourcefulness(self):
        """Oblicza zaradność na podstawie aktualnych parametrów."""
        base_resourcefulness = self.resourcefulness

        # Czynniki zwiększające zaradność
        if self.age > 40:
            # Wzrasta proporcjonalnie z wiekiem (doświadczenie)
            base_resourcefulness += min(15, (self.age - 40) / 4)

        if self.health > 60:
            base_resourcefulness += 4
        if self.hunger < 50:
            base_resourcefulness += 2
        if self.thirst < 50:
            base_resourcefulness += 2
        if self.population > 40:
            base_resourcefulness += 3

        # Tu można by dodać mechanizm uczenia się z przetrwanych trudnych okresów

        # Czynniki zmniejszające zaradność
        if self.health < 40:
            base_resourcefulness -= 5
        if self.hunger > 70:
            base_resourcefulness -= 6
        if self.thirst > 70:
            base_resourcefulness -= 6
        if self.population < 30:
            base_resourcefulness -= 4

        weather = self.model.environment.weather_condition
        if weather > 80:
            base_resourcefulness -= 5

        # Ograniczenie wartości do zakresu 1-100
        self.resourcefulness = max(1, min(100, base_resourcefulness))

    def calculate_endurance(self):
        """Oblicza wytrzymałość na podstawie aktualnych parametrów."""
        base_endurance = self.endurance

        # Czynniki zwiększające wytrzymałość
        # Jeśli agent nie migruje, wytrzymałość się regeneruje
        if not hasattr(self, 'last_migrated') or self.model.current_period - self.last_migrated > 1:
            base_endurance += 5

        if self.health > 70:
            base_endurance += 4
        if self.resourcefulness > 60:
            base_endurance += 3
        if self.food_supply > 60:
            base_endurance += 2
        if self.water_supply > 60:
            base_endurance += 2

        # Czynniki zmniejszające wytrzymałość
        if self.health < 50:
            base_endurance -= 3
        if self.hunger > 60:
            base_endurance -= 4
        if self.thirst > 60:
            base_endurance -= 5

        field = self.model.environment.map.get_field(self.position)
        if field and field.terrain_difficulty > 70:
            base_endurance -= 3

        weather = self.model.environment.weather_condition
        if weather > 80:
            base_endurance -= 5

        if self.population > 90:
            base_endurance -= 4  # Zbyt duża grupa do efektywnego przemieszczania

        # Ograniczenie wartości do zakresu 1-100
        self.endurance = max(1, min(100, base_endurance))

    def update_hunger(self):
        """Aktualizuje poziom głodu."""
        base_hunger = self.hunger

        # Czynniki zwiększające głód
        if self.food_supply < 30:
            base_hunger += 8

        # Naturalny przyrost głodu z czasem
        base_hunger += 3

        if self.endurance < 40:
            base_hunger += 2
        if self.population > 70:
            base_hunger += 3

        weather = self.model.environment.weather_condition
        if weather > 70:  # Niesprzyjające warunki pogodowe
            base_hunger += 2

        # Czynniki zmniejszające głód
        if self.food_supply > 60:
            base_hunger -= 5
        if self.resourcefulness > 70:
            base_hunger -= 3

        # Ograniczenie wartości do zakresu 1-100
        self.hunger = max(1, min(100, base_hunger))

    def update_thirst(self):
        """Aktualizuje poziom pragnienia."""
        base_thirst = self.thirst

        # Czynniki zwiększające pragnienie
        if self.water_supply < 30:
            base_thirst += 10

        # Naturalny przyrost pragnienia z czasem
        base_thirst += 4

        if self.endurance < 40:
            base_thirst += 3
        if self.population > 70:
            base_thirst += 3

        weather = self.model.environment.weather_condition
        if weather > 70:  # Niesprzyjające warunki pogodowe (np. upały)
            base_thirst += 5

        # Czynniki zmniejszające pragnienie
        if self.water_supply > 60:
            base_thirst -= 7
        if self.resourcefulness > 70:
            base_thirst -= 3

        weather = self.model.environment.weather_condition
        if weather < 30:  # Sprzyjające warunki (np. deszcze)
            base_thirst -= 2

        # Ograniczenie wartości do zakresu 1-100
        self.thirst = max(1, min(100, base_thirst))

    def update_health(self):
        """Aktualizuje poziom zdrowia na podstawie parametrów."""
        base_health = self.health

        # Czynniki zwiększające zdrowie
        if self.hunger < 30:
            base_health += 3
        if self.thirst < 30:
            base_health += 3

        field = self.model.environment.map.get_field(self.position)
        if field and field.danger < 40:
            base_health += 2
        if self.age < 35:
            base_health += 2

        # Czynniki zmniejszające zdrowie
        if self.hunger > 70:
            base_health -= 5
        if self.thirst > 70:
            base_health -= 7
        if field and field.danger > 60:
            base_health -= 4
        if self.mortality > 60:
            base_health -= 3
        if self.age > 45:
            base_health -= 2

        weather = self.model.environment.weather_condition
        if weather > 80:
            base_health -= 5

        # Ograniczenie wartości do zakresu 1-100
        self.health = max(1, min(100, base_health))