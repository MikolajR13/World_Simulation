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
        return ('<p style="color:blue; font-weight:bold;">INFO: The map visualization has a fixed size (50x50).'
                ' Changing the sliders and clicking `Reset` will change the *actual* simulation area inside this grid.</p>')


class LegendElement(TextElement):
    """ Wyświetla legendę dla wizualizacji agentów. """
    def render(self, model):
        legend_html = """
        <h4>Legend (Trait-Based):</h4>
        <ul style="list-style-type:none; padding: 0;">
            <li><span style="color:green; font-size: 1.5em;">●</span> <b>Stable:</b> Standard tribe.</li>
            <li><span style="color:red; font-size: 1.5em;">●</span> <b>Warlike:</b> History of many conflicts.</li>
            <li><span style="color:brown; font-size: 1.5em;">●</span> <b>Survivor:</b> Endured many crises.</li>
            <li><span style="color:gold; font-size: 1.5em;">●</span> <b>Prosperous:</b> History of prosperity.</li>
            <li><span style="color:purple; font-size: 1.5em;">●</span> <b>Established:</b> Very old tribe.</li>
            <hr>
            <li><span style="color:blue; display:inline-block; width:12px; height:12px; background-color:blue; vertical-align: middle; margin-right: 3px;"></span> <i>(Overlay)</i> Migrating (current step).</li>
            <li><i>(Border)</i> High Aggression (current).</li>
            <li><i>(Opacity)</i> Current Health.</li>
            <li><i>(Size)</i> Current Population.</li>
        </ul>
        """
        return legend_html


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
        "Layer": 1,
        "r": 0.5 + agent.population / 200,
        "Shape": "circle",
        "opacity": max(0.4, agent.health / 100)
    }

    # --- Ustalanie wyglądu wg CECHY DOMINUJĄCEJ ---
    trait = agent.dominant_trait
    if trait == "Warlike":
        portrayal["Color"] = "red"
    elif trait == "Survivor":
        portrayal["Color"] = "brown"
    elif trait == "Prosperous":
        portrayal["Color"] = "gold"
    elif trait == "Established":
         portrayal["Color"] = "purple"
    else: # Stable or default
        portrayal["Color"] = "green"

    # --- MODYFIKATORY BIEŻĄCEGO STANU ---
    # Migracja ma wysoki priorytet wizualny - zmienia kształt i kolor
    if agent.last_migrated == agent.model.current_period:
        portrayal["Shape"] = "rect"
        portrayal["w"] = 0.8 * portrayal["r"] * 2
        portrayal["h"] = 0.8 * portrayal["r"] * 2
        portrayal["Color"] = "blue"

    # Wysoka agresja (jeśli nie migruje) dodaje czerwoną obwódkę
    if agent.aggression > 70 and portrayal["Shape"] == "circle":
        portrayal["stroke_color"] = "#FF0000" # Czerwona obwódka

    # Kryzys (jeśli nie migruje) zmniejsza rozmiar/opacity
    if (agent.hunger > 80 or agent.thirst > 80) and portrayal["Shape"] == "circle":
         portrayal["r"] *= 0.8
         portrayal["opacity"] = max(0.3, portrayal["opacity"] * 0.7)


    # --- Tooltip  ---
    portrayal["ID"] = agent.unique_id
    portrayal["Trait"] = agent.dominant_trait # Pokazujemy cechę!
    portrayal["Population"] = int(agent.population)
    portrayal["Health"] = int(agent.health)
    portrayal["Age"] = round(agent.age, 1)
    portrayal["Aggression"] = int(agent.aggression)
    portrayal["Wars Won"] = agent.wars_won
    portrayal["Crises Survived"] = agent.crises_survived
    portrayal["Migrations"] = agent.migrations_count

    return portrayal


def create_server():
    # Definiujemy parametry wejściowe
    model_params = {
        "map_width": UserSettableParameter("slider", "Map Width", 20, 5, 50, 1,
                                           description="Map width (requires server restart)"),
        "map_height": UserSettableParameter("slider", "Map Height", 20, 5, 50, 1,
                                            description="Map height (requires server restart)"),
        "num_agents": UserSettableParameter("slider", "Number of Agents", 5, 1, 20, 1,
                                            description="Number of agents (works after ‘Reset’)")
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

    visualization_elements = [InfoDisplay(), SeasonDisplay(), grid, LegendElement()] + charts

    # Tworzymy serwer - przekazujemy KLASĘ modelu i LISTĘ elementów
    server = ModularServer(
        SimulationModel,
        visualization_elements,
        "Agent-Based Simulation of Societies",
        model_params
    )

    return server
