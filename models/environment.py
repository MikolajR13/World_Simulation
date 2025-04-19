"""
Moduł definiujący klasę Environment (Środowisko) dla symulacji.
"""
import numpy as np
from typing import List

from utils.enums import Season
from models.map import Map


class Environment:
    """
    Klasa reprezentująca środowisko w symulacji.
    """

    def __init__(self, map_obj: Map):
        """
        Inicjalizuje środowisko z podaną mapą.

        Args:
            map_obj (Map): Obiekt mapy
        """
        self.map = map_obj
        self.season = Season.SPRING
        self.weather_condition = 50

    def update_resources(self):
        """Aktualizuje zasoby na wszystkich polach mapy."""
        for y in range(self.map.height):
            for x in range(self.map.width):
                field = self.map.fields[y][x]
                field.update_resources(self.season, self.weather_condition)

    def impact_on_agents(self, agents):
        """
        Określa wpływ środowiska na agentów.

        Args:
            agents (List): Lista agentów w symulacji
        """
        for agent in agents:
            field = self.map.get_field(agent.position)
            if field:
                field.determine_impact_on_agent(agent)

    def check_interactions_between_agents(self, agents):
        """
        Sprawdza interakcje między agentami na tych samych polach.

        Args:
            agents (List): Lista agentów w symulacji
        """
        agent_positions = {}
        for agent in agents:
            if agent.position not in agent_positions:
                agent_positions[agent.position] = []
            agent_positions[agent.position].append(agent)

        for position, agents_on_field in agent_positions.items():
            if len(agents_on_field) > 1:
                for i in range(len(agents_on_field)):
                    for j in range(i + 1, len(agents_on_field)):
                        agent1, agent2 = agents_on_field[i], agents_on_field[j]
                        # Tutaj mogą być sprawdzane różne interakcje między agentami
                        # Te interakcje są już zaimplementowane w funkcji check_interactions_with_agents
                        # w klasie Agent, więc tutaj możemy je pominąć

    def generate_random_event(self):
        """Generuje losowe zdarzenia wpływające na środowisko lub agentów."""
        # Lista możliwych zdarzeń losowych
        events = [
            "drought",  # Susza
            "flood",  # Powódź
            "plague",  # Zaraza
            "abundant_harvest",  # Obfite zbiory
            "migration",  # Migracja zwierząt
            "natural_disaster"  # Katastrofa naturalna
        ]

        # Losowanie zdarzenia z różnym prawdopodobieństwem w zależności od sezonu
        probabilities = {
            Season.SPRING: [0.05, 0.20, 0.10, 0.40, 0.15, 0.10],
            Season.SUMMER: [0.30, 0.05, 0.15, 0.30, 0.10, 0.10],
            Season.AUTUMN: [0.10, 0.15, 0.20, 0.35, 0.10, 0.10],
            Season.WINTER: [0.05, 0.10, 0.30, 0.05, 0.30, 0.20]
        }

        event = np.random.choice(events, p=probabilities[self.season])

        # Implementacja efektów zdarzeń
        if event == "drought":
            # Zmniejszenie dostępności wody na wszystkich polach
            for y in range(self.map.height):
                for x in range(self.map.width):
                    self.map.fields[y][x].water_availability = max(
                        0, self.map.fields[y][x].water_availability - 20
                    )
            # Pogorszenie warunków pogodowych
            self.weather_condition = min(100, self.weather_condition + 25)

        elif event == "flood":
            # Zwiększenie dostępności wody, ale też niebezpieczeństwa i trudności terenu
            for y in range(self.map.height):
                for x in range(self.map.width):
                    field = self.map.fields[y][x]
                    field.water_availability = min(100, field.water_availability + 30)
                    field.danger = min(100, field.danger + 15)
                    field.terrain_difficulty = min(100, field.terrain_difficulty + 20)

        elif event == "plague":
            # Wpływ zarazy będzie zaimplementowany w funkcji impact_on_agents
            # Zwiększamy niebezpieczeństwo na polach
            for y in range(self.map.height):
                for x in range(self.map.width):
                    self.map.fields[y][x].danger = min(
                        100, self.map.fields[y][x].danger + 25
                    )

        elif event == "abundant_harvest":
            # Zwiększenie dostępności jedzenia
            for y in range(self.map.height):
                for x in range(self.map.width):
                    self.map.fields[y][x].food_availability = min(
                        100, self.map.fields[y][x].food_availability + 30
                    )

        elif event == "migration":
            # Losowy wzrost lub spadek dostępności jedzenia na różnych polach
            for y in range(self.map.height):
                for x in range(self.map.width):
                    change = np.random.randint(-20, 40)
                    self.map.fields[y][x].food_availability = max(
                        0, min(100, self.map.fields[y][x].food_availability + change)
                    )

        elif event == "natural_disaster":
            # Wzrost niebezpieczeństwa i trudności terenu, spadek zasobów
            for y in range(self.map.height):
                for x in range(self.map.width):
                    field = self.map.fields[y][x]
                    field.danger = min(100, field.danger + 35)
                    field.terrain_difficulty = min(100, field.terrain_difficulty + 25)
                    field.food_availability = max(0, field.food_availability - 15)
                    field.water_availability = max(0, field.water_availability - 15)

            # Ekstremalne warunki pogodowe
            self.weather_condition = min(100, self.weather_condition + 40)

        return event

    def change_season(self):
        """Zmienia aktualny sezon na następny."""
        seasons = list(Season)
        current_index = seasons.index(self.season)
        next_index = (current_index + 1) % len(seasons)
        self.season = seasons[next_index]

        # Aktualizacja warunku pogodowego po zmianie sezonu
        self.update_weather_condition()

    def update_weather_condition(self):
        """Aktualizuje warunki pogodowe w zależności od sezonu."""
        base_change = np.random.normal(0, 10)  # Losowa zmiana z rozkładem normalnym

        # Modyfikacja zmiany w zależności od sezonu
        if self.season == Season.SPRING:
            base_change -= 5  # Tendencja do poprawy pogody wiosną
        elif self.season == Season.SUMMER:
            base_change += np.random.randint(-10, 15)  # Większa zmienność latem
        elif self.season == Season.AUTUMN:
            base_change += np.random.randint(-5, 10)  # Umiarkowana zmienność jesienią
        elif self.season == Season.WINTER:
            base_change += 5  # Tendencja do pogorszenia pogody zimą

        # Powrót do średniej po ekstremalnych warunkach
        if self.weather_condition > 80:
            base_change -= 15
        elif self.weather_condition < 20:
            base_change += 15

        self.weather_condition = max(0, min(100, self.weather_condition + base_change))