"""
Moduł definiujący klasę Agent dla symulacji (wersja 2.0 – stabilna 300 + tur)
"""
from mesa import Agent as MesaAgent
import numpy as np
from typing import Optional, List

from utils.point import Point


class Agent(MesaAgent):
    """
    Klasa reprezentująca społeczeństwo/plemię w symulacji.
    """

    # ------------------------------------------------------------------ #
    #                           INICJALIZACJA                            #
    # ------------------------------------------------------------------ #
    def __init__(self, unique_id: int, model, position: Point = None):
        super().__init__(unique_id, model)

        # Parametry życiowe
        self.health = 50
        self.age = 40
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
        self.last_migrated = -1  # znacznik ostatniej migracji

        # Atrybuty pamięci
        self.wars_won = 0
        self.wars_lost = 0
        self.crises_survived = 0
        self.migrations_count = 0
        self.prosperity_periods = 0
        self.dominant_trait = "Stable"  # Możliwe: Stable, Warlike, Survivor, Prosperous, Nomadic

    # ------------------------------------------------------------------ #
    #                       AKTUALIZACJA POPULACJI                       #
    # ------------------------------------------------------------------ #
    def update_population(self):
        """Aktualizuje liczebność populacji."""
        new_population = (
            self.population
            + self.population * (self.fertility / 200)
            - self.population * (self.mortality / 200)
        )
        self.population = max(1, min(100, new_population))
        self.update_age()

    # ------------------------------------------------------------------ #
    #   DODATKOWE METODY, KTÓRYCH BRAKOWAŁO W ORYGINALNYM SZABLONIE      #
    # ------------------------------------------------------------------ #
    def update_age(self):
        """Aktualizuje średni wiek społeczeństwa."""
        growth = max(0, self.population * self.fertility / 200)
        if self.population + growth > 0:
            self.age = ((self.age * self.population) + growth) / (self.population + growth)
        self.age = min(100, self.age + 0.1)

    # ----------------------------- ZASOBY ----------------------------- #
    def collect_food_supply(self):
        """Zbiera zapasy jedzenia z aktualnego pola."""
        field = self.model.environment.map.get_field(self.position)
        if field and field.food_availability > 0:
            amount = min(20, field.food_availability) * (self.resourcefulness / 100)
            self.food_supply = min(100, self.food_supply + amount)
            field.food_availability -= amount

    def collect_water_supply(self):
        """Zbiera zapasy wody z aktualnego pola."""
        field = self.model.environment.map.get_field(self.position)
        if field and field.water_availability > 0:
            amount = min(20, field.water_availability) * (self.resourcefulness / 100)
            self.water_supply = min(100, self.water_supply + amount)
            field.water_availability -= amount

    def consume_food_supply(self):
        """Zużywa zapasy jedzenia proporcjonalnie do liczebności."""
        self.food_supply = max(0, self.food_supply - self.population / 300)

    def consume_water_supply(self):
        """Zużywa zapasy wody proporcjonalnie do liczebności."""
        self.water_supply = max(0, self.water_supply - self.population / 300)

    # ----------------------------- MIGRACJA ---------------------------- #
    def migrate(self):
        """Przemieszcza agenta do korzystniejszego pola."""
        if self.endurance < 6:
            return  # Za mało wytrzymałości

        best_terrains = self.model.environment.map.find_most_favorable_terrain(
            self.position, radius=4
        )
        if not best_terrains:
            return

        new_pos = best_terrains[0]
        current_field = self.model.environment.map.get_field(self.position)
        migration_cost = 5 * (1 + current_field.terrain_difficulty / 100)

        if self.endurance >= migration_cost:
            try:
                # Jeżeli model używa gridu Mesy – przesuń agenta wizualnie
                self.model.grid.move_agent(self, (new_pos.x, new_pos.y))
            except Exception:
                pass
            self.position = new_pos
            self.endurance -= migration_cost
            # Zwiększone zużycie zasobów podczas migracji
            self.consume_food_supply()
            self.consume_water_supply()
            self.last_migrated = self.model.current_period
            self.migrations_count += 1

    # ------------------------------------------------------------------ #
    #                         INTERAKCJE AGENTÓW                         #
    # ------------------------------------------------------------------ #
    def check_interactions_with_agents(self):
        for agent in self.model.schedule.agents:
            if agent.unique_id != self.unique_id and agent.position == self.position:
                if self.aggression > 70 and agent.population < self.population:
                    self.attack_agent(agent)
                elif self.trust > 70 and agent.trust > 50:
                    self.merge_tribes(agent)

    def attack_agent(self, agent) -> bool:
        """Atakuje innego agenta."""
        success_prob = (self.population / agent.population) * (self.aggression / 100)
        if np.random.random() < success_prob:
            agent.health -= 20
            self.food_supply = min(100, self.food_supply + agent.food_supply * 0.5)
            self.water_supply = min(100, self.water_supply + agent.water_supply * 0.5)
            agent.food_supply *= 0.5
            agent.water_supply *= 0.5
            self.model.conflicts_this_step += 1
            self.wars_won += 1
            agent.wars_lost += 1
            self.model.conflicts_this_step += 1
            return True
        else:
            self.wars_lost += 1
            agent.wars_won += 1  # Broniący się "wygrywa"
            self.model.conflicts_this_step += 1  # Nadal był konflikt
        return False

    def merge_tribes(self, agent) -> bool:
        """Łączy dwa plemiona, jeśli warunek ufności jest spełniony."""
        if np.random.random() < (self.trust + agent.trust) / 200:
            # scalanie populacji i parametrów
            self.population += agent.population
            self.health = (self.health + agent.health) / 2
            self.age = (
                self.age * self.population + agent.age * agent.population
            ) / (self.population + agent.population)
            self.fertility = (self.fertility + agent.fertility) / 2
            self.mortality = (self.mortality + agent.mortality) / 2
            self.aggression = (
                self.aggression * self.population + agent.aggression * agent.population
            ) / (self.population + agent.population)
            self.trust = (
                self.trust * self.population + agent.trust * agent.population
            ) / (self.population + agent.population)
            self.resourcefulness = (
                self.resourcefulness * self.population
                + agent.resourcefulness * agent.population
            ) / (self.population + agent.population)
            self.food_supply = min(100, self.food_supply + agent.food_supply)
            self.water_supply = min(100, self.water_supply + agent.water_supply)
            self.model.schedule.remove(agent)
            self.model.grid.remove_agent(agent)

            self.model.mergers_this_step += 1

            return True
        return False

    def update_dominant_trait(self):
        """ Aktualizuje dominujący 'charakter' plemienia na podstawie historii. """
        traits = {
            "Warlike": self.wars_won,
            "Survivor": self.crises_survived,
            "Nomadic": self.migrations_count,
            "Prosperous": self.prosperity_periods
        }

        # Znajdź cechę z najwyższym wynikiem (i jeśli przekracza pewien próg, np. 3)
        max_trait = "Stable"
        max_value = 3  # Próg, aby cecha stała się dominująca

        for trait, value in traits.items():
            if value > max_value:
                max_value = value
                max_trait = trait

        # Jeśli plemię jest bardzo stare i stabilne, może to być jego cecha
        if max_trait == "Stable" and self.age > 60:
            max_trait = "Established"  # Dodajemy nową cechę "Ugruntowane"

        self.dominant_trait = max_trait
    # ------------------------------------------------------------------ #
    #                           GŁÓWNY KROK                             #
    # ------------------------------------------------------------------ #
    def step(self):
        """Wykonuje pojedynczy krok agenta w symulacji."""
        # Sprawdzanie kryzysu i dobrobytu
        is_in_crisis_now = self.hunger > 80 or self.thirst > 80 or self.health < 20
        is_prosperous_now = self.food_supply > 80 and self.water_supply > 80 and self.health > 80

        if is_in_crisis_now:
            self.crises_survived += 1 # Liczymy każdy krok w kryzysie
        if is_prosperous_now:
            self.prosperity_periods += 1

        # --- 1. Aktualizacje podstawowych potrzeb ---
        self.update_hunger()
        self.update_thirst()
        self.update_health()
        self.update_population()

        # --- 2. Zbieranie zasobów ---
        if self.hunger > 45:
            self.collect_food_supply()
        if self.thirst > 45:
            self.collect_water_supply()

        # --- 3. Zużycie zasobów ---
        self.consume_food_supply()
        self.consume_water_supply()

        # --- 4. Decyzja o migracji ---
        if (self.hunger > 40 or self.thirst > 40) and self.endurance > 6:
            self.migrate()

        # --- 5. Interakcje społeczne ---
        self.check_interactions_with_agents()

        # --- 6. Parametry społeczne i wytrzymałość ---
        self.calculate_fertility()
        self.calculate_mortality()
        self.calculate_aggression()
        self.calculate_trust()
        self.calculate_resourcefulness()
        self.calculate_endurance()

        # --- 7. Upływ czasu ---
        self.progress_to_next_period()

        # --- 8. Aktualizacja cechy co 25 kroków ---
        if self.model.current_period % 25 == 0:
            self.update_dominant_trait()

    # ------------------------------------------------------------------ #
    #                KALKULATORY PARAMETRÓW SPOŁECZNYCH                  #
    # ------------------------------------------------------------------ #
    def calculate_fertility(self):
        base = self.fertility
        if self.health > 70:
            base += 5
        if self.hunger < 40:
            base += 3
        if self.thirst < 40:
            base += 3
        if 30 < self.population < 90:
            base += 2
        if self.age < 35:
            base += 4
        if self.hunger > 60:
            base -= 5
        if self.thirst > 60:
            base -= 5
        if self.health < 40:
            base -= 5
        field = self.model.environment.map.get_field(self.position)
        if field and field.danger > 70:
            base -= 4
        if self.population > 90 or self.population < 30:
            base -= 6
        if self.age > 50:
            base -= 4
        self.fertility = max(1, min(100, base))

    def calculate_mortality(self):
        base = self.mortality
        if self.health < 40:
            base += 7
        if self.hunger > 80:
            base += 9
        if self.thirst > 80:
            base += 11
        if self.age > 45:
            base += (self.age - 45) / 5
        field = self.model.environment.map.get_field(self.position)
        if field and field.danger > 70:
            base += 7
        if self.model.environment.weather_condition > 80:
            base += 5
        if self.aggression > 80:
            base += 3
        if self.health > 70:
            base -= 5
        if self.hunger < 40:
            base -= 3
        if self.thirst < 40:
            base -= 3
        if field and field.danger < 30:
            base -= 2
        if self.age < 35:
            base -= 4
        self.mortality = max(1, min(100, base))

    def calculate_aggression(self):
        base = self.aggression
        if self.hunger > 70:
            base += 7
        if self.thirst > 70:
            base += 7
        if self.population > 80:
            base += 5
        if self.trust < 30:
            base += 6
        if self.resourcefulness < 30:
            base += 4
        if self.food_supply < 30:
            base += 5
        if self.water_supply < 30:
            base += 5
        if self.trust > 70:
            base -= 6
        if self.food_supply > 80:
            base -= 5
        if self.water_supply > 80:
            base -= 5
        if self.population < 30:
            base -= 3
        if self.health < 30:
            base -= 4
        if self.resourcefulness > 70:
            base -= 6
        self.aggression = max(1, min(100, base))

    def calculate_trust(self):
        base = self.trust
        if self.food_supply > 80:
            base += 6
        if self.water_supply > 80:
            base += 6
        field = self.model.environment.map.get_field(self.position)
        if field and field.danger < 40:
            base += 4
        if self.resourcefulness > 70:
            base += 5
        if self.health > 70:
            base += 4
        if field and field.danger > 60:
            base -= 6
        if self.hunger > 70:
            base -= 5
        if self.thirst > 70:
            base -= 5
        if self.aggression > 70:
            base -= 6
        if self.model.environment.weather_condition > 80:
            base -= 4
        self.trust = max(1, min(100, base))

    def calculate_resourcefulness(self):
        base = self.resourcefulness
        if self.age > 40:
            base += min(15, (self.age - 40) / 4)
        if self.health > 60:
            base += 4
        if self.hunger < 50:
            base += 2
        if self.thirst < 50:
            base += 2
        if self.population > 40:
            base += 3
        if self.health < 40:
            base -= 5
        if self.hunger > 70:
            base -= 6
        if self.thirst > 70:
            base -= 6
        if self.population < 30:
            base -= 4
        if self.model.environment.weather_condition > 80:
            base -= 5
        self.resourcefulness = max(1, min(100, base))

    def calculate_endurance(self):
        base = self.endurance
        # silniejsza regeneracja
        if self.last_migrated == -1 or self.model.current_period - self.last_migrated > 1:
            base += 10
        if self.health > 70:
            base += 4
        if self.resourcefulness > 60:
            base += 3
        if self.food_supply > 60:
            base += 2
        if self.water_supply > 60:
            base += 2
        if self.health < 50:
            base -= 2
        if self.hunger > 60:
            base -= 3
        if self.thirst > 60:
            base -= 4
        field = self.model.environment.map.get_field(self.position)
        if field and field.terrain_difficulty > 70:
            base -= 2
        if self.model.environment.weather_condition > 80:
            base -= 4
        if self.population > 90:
            base -= 3
        self.endurance = max(1, min(100, base))

    # ------------------------------------------------------------------ #
    #             AKTUALIZACJE GŁODU, PRAGNIENIA, ZDROWIA                #
    # ------------------------------------------------------------------ #
    def update_hunger(self):
        base = self.hunger + 1
        if self.food_supply < 30:
            base += 7
        if self.endurance < 40:
            base += 2
        if self.population > 70:
            base += 2
        if self.model.environment.weather_condition > 70:
            base += 1
        if self.food_supply > 50:
            base -= 5
        if self.resourcefulness > 70:
            base -= 3
        self.hunger = max(1, min(100, base))

    def update_thirst(self):
        base = self.thirst + 1
        if self.water_supply < 30:
            base += 9
        if self.endurance < 40:
            base += 2
        if self.population > 70:
            base += 2
        if self.model.environment.weather_condition > 70:
            base += 2
        if self.water_supply > 50:
            base -= 7
        if self.resourcefulness > 70:
            base -= 3
        if self.model.environment.weather_condition < 30:
            base -= 2
        self.thirst = max(1, min(100, base))

    def update_health(self):
        field = self.model.environment.map.get_field(self.position)
        base = self.health
        if self.hunger < 30:
            base += 5
        if self.thirst < 30:
            base += 5
        if self.food_supply > 50 and self.water_supply > 50:
            base += 4
        if field and field.danger < 40:
            base += 2
        if self.age < 35:
            base += 2
        if self.hunger > 70:
            base -= 4
        if self.thirst > 70:
            base -= 6
        if field and field.danger > 60:
            base -= 3
        if self.mortality > 60:
            base -= 3
        if self.age > 45:
            base -= 2
        if self.model.environment.weather_condition > 80:
            base -= 2
        self.health = max(1, min(100, base))

    # ------------------------------------------------------------------ #
    #                   UPŁYW OKRESU (wiek +0.1)                         #
    # ------------------------------------------------------------------ #
    def progress_to_next_period(self):
        self.age = min(100, self.age + 0.1)
