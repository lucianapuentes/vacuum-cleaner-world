import pandas as pd
import matplotlib.pyplot as plt

# Archivo CSV con los runs
CSV_FILE = "agent_runs2.csv"

def main():
    # Leer CSV
    df = pd.read_csv(CSV_FILE)

    # Convertir size a texto para usarlo en los ejes
    df["size"] = df["size"].astype(str)

    # --- Gráfico 1: Performance promedio por entorno y suciedad ---
    perf = df.groupby(["size", "dirt_rate"])["performance"].mean().reset_index()

    for dirt in sorted(df["dirt_rate"].unique()):
        subset = perf[perf["dirt_rate"] == dirt]
        plt.plot(subset["size"], subset["performance"], marker="o", label=f"Dirt {dirt}")

    plt.title("Performance promedio por entorno y suciedad")
    plt.xlabel("Tamaño del entorno")
    plt.ylabel("Performance promedio")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("performance.png")
    plt.clf()

    # --- Gráfico 2: Acciones promedio ---
    actions = df.groupby(["size", "dirt_rate"])["total_actions"].mean().reset_index()

    for dirt in sorted(df["dirt_rate"].unique()):
        subset = actions[actions["dirt_rate"] == dirt]
        plt.plot(subset["size"], subset["total_actions"], marker="o", label=f"Dirt {dirt}")

    plt.title("Acciones promedio por entorno y suciedad")
    plt.xlabel("Tamaño del entorno")
    plt.ylabel("Acciones promedio")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("actions.png")
    plt.clf()

    # --- Gráfico 3: Tiempo promedio ---
    times = df.groupby(["size", "dirt_rate"])["execution_time"].mean().reset_index()

    for dirt in sorted(df["dirt_rate"].unique()):
        subset = times[times["dirt_rate"] == dirt]
        plt.plot(subset["size"], subset["execution_time"], marker="o", label=f"Dirt {dirt}")

    plt.title("Tiempo promedio por entorno y suciedad")
    plt.xlabel("Tamaño del entorno")
    plt.ylabel("Tiempo (segundos)")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("times.png")
    plt.clf()
# --- Gráfico 4: Tierra total vs limpiada ---
    dirt_stats = df.groupby(["total_cells", "dirt_rate"])[["total_dirt", "performance"]].mean().reset_index()
    dirt_stats = dirt_stats.sort_values(["total_cells", "dirt_rate"])

    for dirt in sorted(dirt_stats["dirt_rate"].unique()):
        subset = dirt_stats[dirt_stats["dirt_rate"] == dirt]
        plt.plot(subset["total_cells"], subset["total_dirt"], marker="o", linestyle="--", label=f"Total (dirt {dirt})")
        plt.plot(subset["total_cells"], subset["performance"], marker="x", linestyle="-", label=f"Limpiada (dirt {dirt})")

    plt.title("Tierra total vs limpiada (promedio)")
    plt.xlabel("Cantidad de celdas en el entorno")
    plt.ylabel("Celdas")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig("dirt.png")
    plt.clf()

    print("✅ Gráficos generados: performance.png, actions.png, times.png, dirt.png")

if __name__ == "__main__":
    main()

