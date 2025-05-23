"""
Moduł definiujący wizualizację symulacji w przeglądarce.
"""
from mesa.visualization.modules.CanvasGridVisualization import CanvasGrid
from mesa.visualization.modules.ChartVisualization import ChartModule
from mesa.visualization.ModularVisualization import ModularServer
from mesa.visualization.UserParam import UserSettableParameter
from mesa.visualization.modules import TextElement
from utils.enums import Season

from models.simulation import SimulationModel


class SeasonDisplay(TextElement):
    def render(self, model):
        season = model.environment.season
        weather = int(model.environment.weather_condition)
        total_population = model.total_population()
        num_agents = len(model.schedule.agents)
        avg_health = round(model.average_health(), 1)
        avg_aggression = round(model.average_aggression(), 1)
        avg_trust = round(model.average_trust(), 1)

        # Pobieramy aktualne wymiary z modelu
        current_width = model.grid.width
        current_height = model.grid.height

        # Season emojis
        season_emojis = {
            Season.SPRING: "🌸 Spring",
            Season.SUMMER: "☀️ Summer",
            Season.AUTUMN: "🍂 Autumn",
            Season.WINTER: "❄️ Winter"
        }

        # Color-coded weather description
        if weather < 30:
            weather_desc = f'<span style="color:green;"><b>Mild ({weather})</b></span>'
        elif weather < 70:
            weather_desc = f'<span style="color:orange;"><b>Moderate ({weather})</b></span>'
        else:
            weather_desc = f'<span style="color:red;"><b>Extreme ({weather})</b></span>'

        return f"""
            <b>Current Season:</b> {season_emojis[season]}<br>
            <b>Weather Condition:</b> {weather_desc}<br>
            <b>Total Population:</b> {total_population}<br>
            <b>Number of Tribes:</b> {num_agents}<br>
            <b>Avg Health:</b> {avg_health}<br>
            <b>Avg Aggression:</b> {avg_aggression}<br>
            <b>Avg Trust:</b> {avg_trust}<br>
            <b>Current Map Size:</b> {current_width}x{current_height}
        """


class InfoDisplay(TextElement):
    def render(self, model):
        return '<p style="color:blue; font-weight:bold;">INFO: Wizualizacja mapy ma stały rozmiar (50x50). Zmiana suwaków i kliknięcie \'Reset\' zmieni *faktyczny* obszar symulacji wewnątrz tej siatki.</p>'


def agent_portrayal(agent):
    """
    Definiuje wygląd agenta na wizualizacji, w tym tooltip i kształt.

    Args:
        agent: Agent do narysowania

    Returns:
        dict: Słownik z parametrami wyglądu agenta
    """
    if agent is None:
        return

    portrayal = {
        "Filled": "true",
        "Layer": 1,  # Podnosimy agentów na warstwę 1 (jeśli chcemy rysować tło)
        "r": 0.5 + agent.population / 200  # Promień zależny od liczebności
    }

    # --- Dynamiczny Kształt ---
    # Sprawdzamy, czy agent migrował w tej turze
    is_migrating = agent.last_migrated == agent.model.current_period

    if is_migrating:
        portrayal["Shape"] = "rect" # Zmieniamy kształt na prostokąt
        portrayal["w"] = 0.8 * portrayal["r"] * 2 # Szerokość prostokąta
        portrayal["h"] = 0.8 * portrayal["r"] * 2 # Wysokość prostokąta
        portrayal["Color"] = "blue" # Inny kolor dla migrujących
    elif agent.aggression > 70:
        portrayal["Shape"] = "circle" # Kółko
        portrayal["Color"] = "red" # Kolor czerwony dla agresywnych
    elif agent.aggression > 40:
        portrayal["Shape"] = "circle"
        portrayal["Color"] = "orange"  # Pomarańczowy dla średnio agresywnych
    else:
        portrayal["Shape"] = "circle"
        portrayal["Color"] = "green"  # Zielony dla pokojowych

    # Przezroczystość zależna od zdrowia (bez zmian)
    portrayal["opacity"] = max(0.4, agent.health / 100)

    portrayal["ID"] = agent.unique_id
    portrayal["Population"] = int(agent.population)
    portrayal["Health"] = int(agent.health)
    portrayal["Aggression"] = int(agent.aggression)
    portrayal["Trust"] = int(agent.trust)
    portrayal["Food"] = int(agent.food_supply)
    portrayal["Water"] = int(agent.water_supply)
    portrayal["Hunger"] = int(agent.hunger)
    portrayal["Thirst"] = int(agent.thirst)
    portrayal["Endurance"] = int(agent.endurance)

    return portrayal


def create_server():
    # Definiujemy parametry wejściowe
    model_params = {
        "map_width": UserSettableParameter("slider", "Map Width", 20, 5, 50, 1,
                                           description="Szerokość mapy (wymaga restartu serwera)"),
        "map_height": UserSettableParameter("slider", "Map Height", 20, 5, 50, 1,
                                            description="Wysokość mapy (wymaga restartu serwera)"),
        "num_agents": UserSettableParameter("slider", "Number of Agents", 5, 1, 20, 1,
                                            description="Liczba agentów (działa po 'Reset')")
    }

    # Ustawiamy MAKSYMALNE wymiary siatki na stałe
    max_width = 20
    max_height = 20

    # Tworzymy CanvasGrid RAZ z wymiarami początkowymi.
    grid = CanvasGrid(agent_portrayal, max_width, max_height, 600, 600)

    # podstawowe wartości
    # max_width = 20
    # max_height = 50
    # grid = CanvasGrid(agent_portrayal, max_width, max_height, 500, 500)

    # Definiujemy wykresy
    charts = [
        ChartModule([{"Label": "Number_of_agents", "Color": "black"}]),
        ChartModule([
            {"Label": "Average_health", "Color": "blue"},
            {"Label": "Average_population", "Color": "red"}
        ]),
        ChartModule([
            {"Label": "Average_aggression", "Color": "red"},
            {"Label": "Average_trust", "Color": "green"}
        ]),
        ChartModule([{"Label": "Total_population", "Color": "purple"}]),
        ChartModule([{"Label": "Weather_Condition", "Color": "blue"}]),
        ChartModule([
            {"Label": "Average_Hunger", "Color": "brown"},
            {"Label": "Average_Thirst", "Color": "cyan"}
        ], data_collector_name='datacollector'),
        ChartModule([
            {"Label": "Average_Food_Supply", "Color": "lime"},
            {"Label": "Average_Water_Supply", "Color": "deepskyblue"}
        ], data_collector_name='datacollector'),
        ChartModule([
            {"Label": "Average_Age", "Color": "darkgray"}
        ], data_collector_name='datacollector'),
        ChartModule([
            {"Label": "Conflicts", "Color": "magenta"},
            {"Label": "Mergers", "Color": "orange"}
        ], data_collector_name='datacollector')
    ]

    visualization_elements = [InfoDisplay(), SeasonDisplay(), grid] + charts

    # Tworzymy serwer - przekazujemy KLASĘ modelu i LISTĘ elementów
    server = ModularServer(
        SimulationModel,
        visualization_elements,
        "Agent-Based Simulation of Societies",
        model_params
    )

    return server
