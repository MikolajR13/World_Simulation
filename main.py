"""
Główny plik uruchamiający symulację agentową.
"""
import argparse
import pandas as pd
import matplotlib.pyplot as plt
from mesa.batchrunner import BatchRunner

from models.simulation import SimulationModel
from visualization.server import create_server


def run_single_simulation(steps=100, map_width=20, map_height=20, num_agents=5):
    """
    Uruchamia pojedynczą symulację przez określoną liczbę kroków.

    Args:
        steps (int): Liczba kroków symulacji
        map_width (int): Szerokość mapy
        map_height (int): Wysokość mapy
        num_agents (int): Początkowa liczba agentów

    Returns:
        SimulationModel: Model symulacji po wykonaniu
    """
    model = SimulationModel(map_width=map_width, map_height=map_height, num_agents=num_agents)

    for i in range(steps):
        model.step()

    return model


def run_batch_simulation(steps=100, iterations=5):
    """
    Uruchamia serię symulacji z różnymi parametrami.

    Args:
        steps (int): Liczba kroków symulacji
        iterations (int): Liczba iteracji dla każdej kombinacji parametrów

    Returns:
        DataFrame: Ramka danych z wynikami symulacji
    """
    # Definicja parametrów do przetestowania
    parameters = {
        "map_width": [10, 20, 30],
        "map_height": [10, 20, 30],
        "num_agents": [3, 5, 10]
    }

    # Definicja danych do zebrania
    metrics = {
        "Number_of_agents": lambda m: len(m.schedule.agents),
        "Average_health": lambda m: m.average_health(),
        "Average_population": lambda m: m.average_population(),
        "Total_population": lambda m: m.total_population()
    }

    # Uruchomienie symulacji wsadowej
    batch_run = BatchRunner(
        SimulationModel,
        parameters,
        metrics,
        iterations=iterations,
        max_steps=steps,
        model_reporters={"DataCollector": lambda m: m.datacollector}
    )

    batch_run.run_all()

    # Zebranie danych
    data = batch_run.get_model_vars_dataframe()

    return data


def save_simulation_data(model, filename="simulation_results.csv"):
    """
    Zapisuje dane symulacji do pliku CSV.

    Args:
        model (SimulationModel): Model symulacji
        filename (str): Nazwa pliku do zapisu
    """
    model_data = model.datacollector.get_model_vars_dataframe()
    model_data.to_csv(filename)

    # Dodatkowo zapisujemy dane agentów
    agent_data = model.datacollector.get_agent_vars_dataframe()
    agent_data.to_csv(filename.replace(".csv", "_agents.csv"))

    print(f"Dane zostały zapisane do plików {filename} i {filename.replace('.csv', '_agents.csv')}")


def plot_simulation_results(model, save_fig=False):
    """
    Tworzy wykresy z wynikami symulacji.

    Args:
        model (SimulationModel): Model symulacji
        save_fig (bool): Czy zapisać wykresy do plików
    """
    model_data = model.datacollector.get_model_vars_dataframe()

    # Wykres liczby agentów
    plt.figure(figsize=(12, 6))
    plt.subplot(2, 2, 1)
    model_data["Number_of_agents"].plot()
    plt.title("Number of Societies")
    plt.xlabel("Step")
    plt.ylabel("Number")

    # Wykres średniego zdrowia i populacji
    plt.subplot(2, 2, 2)
    model_data[["Average_health", "Average_population"]].plot()
    plt.title("Average Health and Population")
    plt.xlabel("Step")
    plt.ylabel("Value")

    # Wykres średniej agresji i zaufania
    plt.subplot(2, 2, 3)
    model_data[["Average_aggression", "Average_trust"]].plot()
    plt.title("Average Aggression and Trust")
    plt.xlabel("Step")
    plt.ylabel("Value")

    # Wykres całkowitej populacji
    plt.subplot(2, 2, 4)
    model_data["Total_population"].plot()
    plt.title("Total Population")
    plt.xlabel("Step")
    plt.ylabel("Population")

    plt.tight_layout()

    if save_fig:
        plt.savefig("simulation_results.png", dpi=300)
        print("Wykres został zapisany do pliku simulation_results.png")

    plt.show()


def run_server(port=8521):
    """
    Uruchamia serwer wizualizacji.

    Args:
        port (int): Port, na którym będzie działał serwer
    """
    server = create_server()
    server.port = port
    server.launch()
    print(f"Serwer został uruchomiony na porcie {port}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Symulacja agentowa społeczeństw")
    parser.add_argument("--mode", type=str, default="server",
                        choices=["server", "single", "batch"],
                        help="Tryb działania: server, single lub batch")
    parser.add_argument("--steps", type=int, default=100,
                        help="Liczba kroków symulacji")
    parser.add_argument("--width", type=int, default=20,
                        help="Szerokość mapy")
    parser.add_argument("--height", type=int, default=20,
                        help="Wysokość mapy")
    parser.add_argument("--agents", type=int, default=5,
                        help="Liczba agentów")
    parser.add_argument("--port", type=int, default=8521,
                        help="Port serwera wizualizacji")
    parser.add_argument("--save", action="store_true",
                        help="Zapisz wyniki symulacji")
    parser.add_argument("--plot", action="store_true",
                        help="Wygeneruj wykresy wyników")

    args = parser.parse_args()

    if args.mode == "server":
        run_server(port=args.port)
    elif args.mode == "single":
        model = run_single_simulation(steps=args.steps, map_width=args.width,
                                      map_height=args.height, num_agents=args.agents)
        if args.save:
            save_simulation_data(model)
        if args.plot:
            plot_simulation_results(model, save_fig=args.save)
    elif args.mode == "batch":
        data = run_batch_simulation(steps=args.steps)
        if args.save:
            data.to_csv("batch_results.csv")
            print("Wyniki zostały zapisane do pliku batch_results.csv")
        if args.plot:
            # Przykładowy wykres z wynikami wsadowymi
            plt.figure(figsize=(10, 6))
            grouped = data.groupby(["num_agents", "map_width", "map_height"])
            means = grouped.mean()
            means.reset_index()[["num_agents", "Average_health", "Average_population"]].plot(
                x="num_agents",
                y=["Average_health", "Average_population"],
                kind="bar"
            )
            plt.title("Impact of Number of Agents on Health and Population")
            plt.tight_layout()

            if args.save:
                plt.savefig("batch_results.png", dpi=300)
                print("Wykres został zapisany do pliku batch_results.png")

            plt.show()