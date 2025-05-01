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

    # ------------------------------------------------------------------ #
    #                          INICJALIZACJA                             #
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

    # ------------------------------------------------------------------ #
    #                       GŁÓWNA PĘTLA ŻYCIA                           #
    # ------------------------------------------------------------------ #

    def step(self):
        """Wykonuje pojedynczy krok agenta w symulacji."""
        # 1. Aktualizacja podstawowych potrzeb
        self.update_hunger()
        self.update_thirst()
        self.update_health()
        self.update_population()

        # 2. Zbieranie zasobów (zanim nadejdzie krytyczny stan)
        if self.hunger > 45:
            self.collect_food_supply()
        if self.thirst > 45:
            self.collect_water_supply()

        # 3. Zużycie zgromadzonych zapasów
        self.consume_food_supply()
        self.consume_water_supply()

        # 4. Decyzja o migracji ‒ zależna od realnej potrzeby i energii
        if (self.hunger > 50 or self.thirst > 50) and self.endurance > 10:
            self.migrate()

        # 5. Interakcje z innymi agentami
        self.check_interactions_with_agents()

        # 6. Parametry społeczne i wytrzymałość
        self.calculate_fertility()
        self.calculate_mortality()
        self.calculate_aggression()
        self.calculate_trust()
        self.calculate_resourcefulness()
        self.calculate_endurance()

        # 7. Upływ czasu
        self.progress_to_next_period()

    # ------------------------------------------------------------------ #
    #                        ZASOBY – ZBIÓR / KONSUMPCJA                 #
    # ------------------------------------------------------------------ #

    def collect_food_supply(self):
        field = self.model.environment.map.get_field(self.position)
        if field:
            amount = min(15, field.food_availability) * (self.resourcefulness / 100)
            self.food_supply = min(100, self.food_supply + amount)
            field.food_availability = max(0, field.food_availability - amount)

    def collect_water_supply(self):
        field = self.model.environment.map.get_field(self.position)
        if field:
            amount = min(15, field.water_availability) * (self.resourcefulness / 100)
            self.water_supply = min(100, self.water_supply + amount)
            field.water_availability = max(0, field.water_availability - amount)

    def consume_food_supply(self):
        consumption = self.population / 200
        self.food_supply = max(0, self.food_supply - consumption)

    def consume_water_supply(self):
        consumption = self.population / 200
        self.water_supply = max(0, self.water_supply - consumption)

    # ------------------------------------------------------------------ #
    #                             MIGRACJA                               #
    # ------------------------------------------------------------------ #

    def migrate(self):
        """Przemieszcza agenta na korzystniejsze pole."""
        if self.endurance < 15:
            return  # za mało energii

        best_terrains = self.model.environment.map.find_most_favorable_terrain(
            self.position, 3
        )
        if not best_terrains:
            return

        new_position = best_terrains[0]
        current_field = self.model.environment.map.get_field(self.position)
        migration_cost = 10 * (1 + current_field.terrain_difficulty / 100)

        if self.endurance >= migration_cost:
            self.endurance -= migration_cost
            self.position = new_position
            # zużycie zapasów podczas marszu
            self.consume_food_supply()
            self.consume_water_supply()
            self.last_migrated = self.model.current_period

    # ------------------------------------------------------------------ #
    #                         AKTUALIZACJE POTRZEB                       #
    # ------------------------------------------------------------------ #

    def update_hunger(self):
        base = self.hunger
        if self.food_supply < 30:
            base += 8
        base += 2  # łagodniejszy przyrost naturalny
        if self.endurance < 40:
            base += 2
        if self.population > 70:
            base += 3
        if self.model.environment.weather_condition > 70:
            base += 2
        if self.food_supply > 60:
            base -= 5
        if self.resourcefulness > 70:
            base -= 3
        self.hunger = max(1, min(100, base))

    def update_thirst(self):
        base = self.thirst
        if self.water_supply < 30:
            base += 10
        base += 2  # łagodniejszy przyrost naturalny
        if self.endurance < 40:
            base += 3
        if self.population > 70:
            base += 3
        if self.model.environment.weather_condition > 70:
            base += 3
        if self.water_supply > 60:
            base -= 7
        if self.resourcefulness > 70:
            base -= 3
        if self.model.environment.weather_condition < 30:
            base -= 3
        self.thirst = max(1, min(100, base))

    def update_health(self):
        base = self.health
        if self.hunger < 30:
            base += 5
        if self.thirst < 30:
            base += 5
        field = self.model.environment.map.get_field(self.position)
        if field and field.danger < 40:
            base += 2
        if self.age < 35:
            base += 2
        if self.hunger > 70:
            base -= 5
        if self.thirst > 70:
            base -= 5
        if field and field.danger > 60:
            base -= 4
        if self.mortality > 60:
            base -= 3
        if self.age > 45:
            base -= 2
        if self.model.environment.weather_condition > 80:
            base -= 3
        self.health = max(1, min(100, base))

    # ------------------------------------------------------------------ #
    #                     POPULACJA I STRUKTURA WIEKOWA                  #
    # ------------------------------------------------------------------ #

    def update_population(self):
        new_pop = self.population + (
            self.population * (self.fertility / 200)
        ) - (self.population * (self.mortality / 200))
        self.population = max(1, min(100, new_pop))
        self.update_age()

    def update_age(self):
        growth = max(0, (self.population * (self.fertility / 200)))
        if self.population + growth > 0:
            self.age = ((self.age * self.population) + (1 * growth)) / (
                self.population + growth
            )
        self.age = min(100, self.age + 0.1)

    def progress_to_next_period(self):
        """Naturalny upływ czasu."""
        self.age = min(100, self.age + 0.1)

    # ------------------------------------------------------------------ #
    #                     INTERAKCJE Z INNYMI AGENTAMI                   #
    # ------------------------------------------------------------------ #

    def check_interactions_with_agents(self):
        for agent in self.model.schedule.agents:
            if agent.unique_id != self.unique_id and agent.position == self.position:
                if self.aggression > 70 and agent.population < self.population:
                    self.attack_agent(agent)
                elif self.trust > 70 and agent.trust > 50:
                    self.merge_tribes(agent)

    def attack_agent(self, agent) -> bool:
        attack_success = (self.population / agent.population) * (self.aggression / 100)
        if np.random.random() < attack_success:
            agent.health -= 20
            self.food_supply = min(100, self.food_supply + agent.food_supply * 0.5)
            self.water_supply = min(100, self.water_supply + agent.water_supply * 0.5)
            agent.food_supply *= 0.5
            agent.water_supply *= 0.5
            return True
        return False

    def merge_tribes(self, agent) -> bool:
        if np.random.random() < (self.trust + agent.trust) / 200:
            # Sumowanie populacji
            self.population += agent.population
            # Średnie parametrów
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
            # Zasoby
            self.food_supply = min(100, self.food_supply + agent.food_supply)
            self.water_supply = min(100, self.water_supply + agent.water_supply)
            # Usuwamy połączone plemię
            self.model.schedule.remove(agent)
            return True
        return False

    # ------------------------------------------------------------------ #
    #                  KALKULATORY PARAMETRÓW SPOŁECZNYCH                #
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
            base += 10
        if self.thirst > 80:
            base += 12
        if self.age > 45:
            base += (self.age - 45) / 5
        field = self.model.environment.map.get_field(self.position)
        if field and field.danger > 70:
            base += 8
        weather = self.model.environment.weather_condition
        if weather > 80:
            base += 6
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
            base += 8
        if self.thirst > 70:
            base += 8
        if self.population > 80:
            base += 5
        if self.trust < 30:
            base += 7
        if self.resourcefulness < 30:
            base += 4
        if self.food_supply < 30:
            base += 6
        if self.water_supply < 30:
            base += 6
        if self.trust > 70:
            base -= 7
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
            base -= 7
        weather = self.model.environment.weather_condition
        if weather > 80:
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
        weather = self.model.environment.weather_condition
        if weather > 80:
            base -= 5
        self.resourcefulness = max(1, min(100, base))

    def calculate_endurance(self):
        base = self.endurance
        if self.last_migrated == -1 or self.model.current_period - self.last_migrated > 1:
            base += 5
        if self.health > 70:
            base += 4
        if self.resourcefulness > 60:
            base += 3
        if self.food_supply > 60:
            base += 2
        if self.water_supply > 60:
            base += 2
        if self.health < 50:
            base -= 3
        if self.hunger > 60:
            base -= 4
        if self.thirst > 60:
            base -= 5
        field = self.model.environment.map.get_field(self.position)
        if field and field.terrain_difficulty > 70:
            base -= 3
        weather = self.model.environment.weather_condition
        if weather > 80:
            base -= 5
        if self.population > 90:
            base -= 4
        self.endurance = max(1, min(100, base))
