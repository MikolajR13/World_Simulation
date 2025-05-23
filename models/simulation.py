"""
Moduł definiujący główną klasę symulacji.
"""
from mesa.model import Model
from mesa.space import MultiGrid
from mesa.time import RandomActivation
from mesa.datacollection import DataCollector
# Usunięto import 'Agent' from mesa.agent, bo jest nieużywany i konfliktuje
from typing import List, Tuple

from utils.point import Point
from models.agent import Agent  # Poprawiony import
from models.map import Map
from models.environment import Environment


class SimulationModel(Model):
    """
    Główna klasa modelu symulacji.
    """

    def __init__(self, map_width=20, map_height=20, num_agents=5):
        """
        Inicjalizuje model symulacji.

        Args:
            map_width (int): Szerokość mapy
            map_height (int): Wysokość mapy
            num_agents (int): Początkowa liczba agentów
        """
        super().__init__()

        # Zapisujemy parametry wejściowe, aby można je było wyświetlić
        self.initial_map_width = map_width
        self.initial_map_height = map_height
        self.initial_num_agents = num_agents

        self.schedule = RandomActivation(self)
        self.grid = MultiGrid(map_width, map_height, True)

        # Inicjalizacja mapy i środowiska
        self.map = Map(map_width, map_height)
        self.environment = Environment(self.map)

        # Parametry symulacji
        self.current_period = 0
        self.running = True # Dodajemy flagę, czy symulacja działa

        # Inicjalizacja agentów
        self.initialize_agents(num_agents)

        # Kolekcja danych do wizualizacji
        self.datacollector = DataCollector(
            model_reporters={
                "Number_of_agents": lambda m: len(m.schedule.agents),
                "Average_health": lambda m: self.average_health(),
                "Average_population": lambda m: self.average_population(),
                "Average_aggression": lambda m: self.average_aggression(),
                "Average_trust": lambda m: self.average_trust(),
                "Total_population": lambda m: self.total_population(),
                "Weather_Condition": lambda m: m.environment.weather_condition,
                # Dodajemy reportery do wyświetlania aktualnych wymiarów
                "Current_Width": lambda m: m.grid.width,
                "Current_Height": lambda m: m.grid.height
            },
            agent_reporters={
                "Health": "health",
                "Population": "population",
                "Aggression": "aggression",
                "Trust": "trust",
                "Food_supply": "food_supply",
                "Water_supply": "water_supply"
            }
        )

        # Usunęliśmy ValueError - nie rozwiąże problemu, a tylko go powoduje.
        # Problem leży w CanvasGrid, a nie w MultiGrid.

    def initialize_agents(self, num_agents):
        """
        Inicjalizuje agentów w losowych pozycjach na mapie.

        Args:
            num_agents (int): Liczba agentów do zainicjalizowania
        """
        # Czyścimy starych agentów, jeśli istnieją (ważne przy resecie)
        self.schedule = RandomActivation(self)
        # Usuwamy agentów z siatki (ważne - MultiGrid może przechowywać stare)
        for cell in self.grid.coord_iter():
            agents, x, y = cell
            for agent in list(agents): # Używamy list() do bezpiecznego usuwania
                 self.grid.remove_agent(agent)

        # Tworzymy nowych agentów
        for i in range(num_agents):
            x = self.random.randrange(self.grid.width)
            y = self.random.randrange(self.grid.height)
            position = Point(x, y)

            agent = Agent(i, self, position)
            self.schedule.add(agent)
            self.grid.place_agent(agent, (x, y))


    def average_health(self):
        """
        Zwraca średnie zdrowie wszystkich agentów.

        Returns:
            float: Średnie zdrowie agentów
        """
        health_values = [agent.health for agent in self.schedule.agents]
        return sum(health_values) / len(health_values) if health_values else 0

    def average_population(self):
        """
        Zwraca średnią liczebność wszystkich agentów.

        Returns:
            float: Średnia liczebność agentów
        """
        population_values = [agent.population for agent in self.schedule.agents]
        return sum(population_values) / len(population_values) if population_values else 0

    def average_aggression(self):
        """
        Zwraca średnią agresję wszystkich agentów.

        Returns:
            float: Średnia agresja agentów
        """
        aggression_values = [agent.aggression for agent in self.schedule.agents]
        return sum(aggression_values) / len(aggression_values) if aggression_values else 0

    def average_trust(self):
        """
        Zwraca średnią ufność wszystkich agentów.

        Returns:
            float: Średnia ufność agentów
        """
        trust_values = [agent.trust for agent in self.schedule.agents]
        return sum(trust_values) / len(trust_values) if trust_values else 0

    def total_population(self):
        """
        Zwraca sumę liczebności wszystkich agentów.

        Returns:
            float: Suma liczebności agentów
        """
        return sum(agent.population for agent in self.schedule.agents)

    def step(self):
        """Wykonuje jeden krok symulacji."""
        # Aktualizacja środowiska
        self.environment.update_resources()
        self.environment.impact_on_agents(self.schedule.agents)

        # Wykonanie kroków przez agentów
        self.schedule.step()

        # Sprawdzenie interakcji między agentami
        self.environment.check_interactions_between_agents(self.schedule.agents)

        # Zdarzenia losowe
        if self.random.random() < 0.1:  # 10% szans na zdarzenie losowe
            self.environment.generate_random_event()

        # Zmiana sezonu co 10 okresów
        if self.current_period % 10 == 0 and self.current_period > 0:
            self.environment.change_season()

        # Zbieranie danych
        self.datacollector.collect(self)

        # Inkrementacja okresu
        self.current_period += 1

    def execute_step(self):
        """Alias dla metody step."""
        self.step()

    def initialize(self):
        """Inicjalizuje model."""
        # Ta metoda może być użyta do resetowania modelu lub dodatkowej konfiguracji
        pass

    def collect_statistics(self):
        """
        Zbiera statystyki symulacji.

        Returns:
            DataFrame: Ramka danych z zebranymi statystykami
        """
        return self.datacollector.get_model_vars_dataframe()

    def detect_conflicts(self):
        """
        Wykrywa konflikty między agentami.

        Returns:
            List[Tuple[Agent, Agent]]: Lista par agentów będących w konflikcie
        """
        conflicts = []
        for i, agent1 in enumerate(self.schedule.agents):
            for j, agent2 in enumerate(self.schedule.agents[i + 1:], i + 1):
                if agent1.position == agent2.position and agent1.aggression > 70:
                    conflicts.append((agent1, agent2))
        return conflicts

    def resolve_conflicts(self):
        """Rozwiązuje wykryte konflikty między agentami."""
        conflicts = self.detect_conflicts()
        for agent1, agent2 in conflicts:
            if agent1.aggression > agent2.aggression:
                agent1.attack_agent(agent2)
            elif agent1.trust > 70 and agent2.trust > 70:
                agent1.merge_tribes(agent2)