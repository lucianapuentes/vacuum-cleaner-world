import csv
from run_agent import load_agent_from_file, run_single_agent

# Configuración de pruebas
ENTORNOS = [(2, 2), (4, 4), (8, 8), (16, 16), (32, 32), (64, 64), (128, 128)]
DIRT_RATES = [0.1, 0.2, 0.4, 0.8]
REPEATS = 10

# Ruta al archivo del agente reflexivo
AGENT_FILE = "agents/reflex_agent.py"   # <- ajustado a tu estructura

# URL del servidor del entorno
SERVER_URL = "http://localhost:5000"

def main():
    agent_class = load_agent_from_file(AGENT_FILE)
    semilla=12345
    results = []

    for (sx, sy) in ENTORNOS:
        for dirt_rate in DIRT_RATES:
            for run in range(REPEATS):
                result = run_single_agent(
                    agent_class,
                    SERVER_URL,
                    sx, sy,
                    dirt_rate,
                    verbose=False,
                    agent_id=run,
                    seed=semilla
                )

                if result["success"]:
                    results.append({
                        "size": f"{sx}x{sy}",
                        "dirt_rate": dirt_rate,
                        "run": run + 1,
                        "performance": result["performance"],
                        "total_actions": result["total_actions"],
                        "execution_time": result["execution_time"],
                        "successful_actions": result["successful_actions"],
                        "success_rate": result["success_rate"],
                        "agent_class": result["agent_class"],
                        "strategy": result["strategy"],
                        "seed": semilla
                    })
                    
                else:
                    print(f"❌ Error en entorno {sx}x{sy}, dirt={dirt_rate}, run={run}: {result['error']}")
            semilla+=1
    # Guardar a CSV con todos los runs
    with open("agent_runs2.csv", "w", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=results[0].keys())
        writer.writeheader()
        writer.writerows(results)

    print("✅ Resultados detallados guardados en agent_runs.csv")

if __name__ == "__main__":
    main()

