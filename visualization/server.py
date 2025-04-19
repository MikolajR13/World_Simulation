"""
Moduł definiujący wizualizację symulacji w przeglądarce.
"""
from mesa.visualization.modules.CanvasGridVisualization import CanvasGrid
from mesa.visualization.modules.ChartVisualization import ChartModule
from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.UserParam import UserSettableParameter

from models.simulation import SimulationModel


def agent_portrayal(agent):
    """
    Definiuje wygląd agenta na wizualizacji.

    Args:
        agent: Agent do narysowania

    Returns:
        dict: Słownik z parametrami wyglądu agenta
    """
    portrayal = {
        "Shape": "circle",
        "Filled": "true",
        "Layer": 0,
        "r": 0.5 + agent.population / 200,  # Promień zależny od liczebności
    }

    # Kolor zależny od poziomu agresji
    if agent.aggression > 70:
        portrayal["Color"] = "red"
    elif agent.aggression > 40:
        portrayal["Color"] = "orange"
    else:
        portrayal["Color"] = "green"

    # Przezroczystość zależna od zdrowia
    portrayal["opacity"] = max(0.4, agent.health / 100)

    return portrayal


def create_server(width=20, height=20):
    """
    Tworzy serwer do wizualizacji symulacji.

    Args:
        width (int): Szerokość mapy
        height (int): Wysokość mapy

    Returns:
        ModularServer: Serwer do wizualizacji
    """
    # Parametry konfiguracyjne dla użytkownika
    model_params = {
        "map_width": UserSettableParameter(
            "slider",
            "Map Width",
            20,
            5,
            50,
            1,
            description="Width of the map"
        ),
        "map_height": UserSettableParameter(
            "slider",
            "Map Height",
            20,
            5,
            50,
            1,
            description="Height of the map"
        ),
        "num_agents": UserSettableParameter(
            "slider",
            "Number of Agents",
            5,
            1,
            20,
            1,
            description="Initial number of societies"
        )
    }

    # Elementy wizualizacji
    grid = CanvasGrid(agent_portrayal, width, height, 500, 500)

    # Wykresy
    charts = [
        ChartModule(
            [{"Label": "Number_of_agents", "Color": "black"}],
            data_collector_name="datacollector",
            canvas_height=100,
            canvas_width=500
        ),
        ChartModule(
            [
                {"Label": "Average_health", "Color": "blue"},
                {"Label": "Average_population", "Color": "red"}
            ],
            data_collector_name="datacollector",
            canvas_height=200,
            canvas_width=500
        ),
        ChartModule(
            [
                {"Label": "Average_aggression", "Color": "red"},
                {"Label": "Average_trust", "Color": "green"}
            ],
            data_collector_name="datacollector",
            canvas_height=200,
            canvas_width=500
        ),
        ChartModule(
            [{"Label": "Total_population", "Color": "purple"}],
            data_collector_name="datacollector",
            canvas_height=100,
            canvas_width=500
        )
    ]

    # Tworzenie serwera
    server = ModularServer(
        SimulationModel,
        [grid] + charts,
        "Agent-Based Simulation of Societies",
        model_params
    )

    return server