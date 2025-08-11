#!/usr/bin/env python3

import sys
import argparse
import time
import random
import importlib.util
from pathlib import Path
from base_agent import BaseAgent

class ReplayAgent(BaseAgent):
    """Minimal agent class used only for replay purposes."""
    
    def think(self, percept: dict) -> str:
        """This method is not used during replay."""
        return 'wait'
    
    def get_strategy_description(self) -> str:
        """Description of the replay strategy."""
        return "Replay Agent - Replaying recorded actions"

def load_agent_from_file(agent_file_path: str):
    """Load an agent class from a Python file."""
    agent_file = Path(agent_file_path)
    
    if not agent_file.exists():
        raise FileNotFoundError(f"Agent file not found: {agent_file_path}")
    
    if not agent_file.suffix == '.py':
        raise ValueError(f"Agent file must be a Python file (.py): {agent_file_path}")
    
    # Load the module from file
    spec = importlib.util.spec_from_file_location("agent_module", agent_file)
    if not spec or not spec.loader:
        raise ImportError(f"Could not load module from {agent_file_path}")
    
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    
    # Find the agent class
    agent_class = None
    for name in dir(module):
        obj = getattr(module, name)
        if (isinstance(obj, type) and 
            hasattr(obj, 'think') and 
            hasattr(obj, 'get_strategy_description') and
            name != 'BaseAgent' and
            not getattr(obj, '__abstractmethods__', None)):
            agent_class = obj
            break
    
    if not agent_class:
        raise ValueError(f"No valid agent class found in {agent_file_path}. Agent must have 'think' and 'get_strategy_description' methods.")
    
    return agent_class

def run_single_agent(agent_class, server_url: str, size_x: int, size_y: int, 
                    dirt_rate: float, verbose: bool, agent_id: int = 0, 
                    enable_ui: bool = False, record_game: bool = False, 
                    replay_file: str = None, cell_size: int = 60, fps: int = 10,
                    auto_exit_on_finish: bool = True, live_stats: bool = False,
                    seed: int = None) -> dict:
    """
    Ejecuta una simulación con un agente específico.
    
    Args:
        agent_class: Clase del agente a ejecutar
        server_url: URL del servidor de entornos
        size_x: Ancho del entorno
        size_y: Alto del entorno
        dirt_rate: Porcentaje de suciedad inicial
        verbose: Si mostrar información detallada
        agent_id: ID del agente (para ejecución en paralelo)
        enable_ui: Si activar la UI pygame
        record_game: Si grabar la simulación
        replay_file: Archivo de replay a reproducir
        cell_size: Tamaño de cada celda en pixels (para UI)
        fps: Frames per second para la UI
        seed: Semilla para reproducibilidad (None para aleatorio)
        
    Returns:
        Diccionario con resultados de la simulación
    """
    start_time = time.time()
    
    # Set random seed if provided
    if seed is not None:
        random.seed(seed)
    
    try:
        # Crear instancia del agente
        agent = agent_class(
            server_url=server_url,
            enable_ui=enable_ui,
            record_game=record_game,
            replay_file=replay_file,
            cell_size=cell_size,
            fps=fps,
            auto_exit_on_finish=auto_exit_on_finish,
            live_stats=live_stats
        )
        
        # Conectar al entorno (solo si no es replay)
        if not replay_file:
            # Always use random starting position
            start_x = random.randint(0, size_x - 1)
            start_y = random.randint(0, size_y - 1)
            connection_success = agent.connect_to_environment(size_x, size_y, dirt_rate, start_x, start_y, seed)
            
            if not connection_success:
                return {
                    'agent_id': agent_id,
                    'agent_class': agent_class.__name__,
                    'success': False,
                    'error': 'Failed to connect to environment',
                    'performance': 0,
                    'execution_time': time.time() - start_time
                }
        
        # Ejecutar simulación
        performance = agent.run_simulation(verbose and agent_id == 0)  # Solo verbose para el primer agente
        execution_time = time.time() - start_time
        
        # Obtener estadísticas finales
        stats = agent.get_statistics()
        
        result = {
            'agent_id': agent_id,
            'agent_class': agent_class.__name__,
            'success': True,
            'performance': performance,
            'execution_time': execution_time,
            'total_actions': stats.get('total_actions', 0),
            'successful_actions': stats.get('successful_actions', 0),
            'success_rate': stats.get('success_rate', 0),
            'strategy': agent.get_strategy_description(),
            'error': None
        }
        
        # Añadir información adicional
        result['ui_enabled'] = enable_ui
        result['recording'] = record_game
        result['replay_mode'] = replay_file is not None
        
        return result
        
    except Exception as e:
        return {
            'agent_id': agent_id,
            'agent_class': agent_class.__name__ if agent_class else 'Unknown',
            'success': False,
            'error': str(e),
            'performance': 0,
            'execution_time': time.time() - start_time
        }
    
    finally:
        try:
            agent.disconnect()
        except:
            pass


def main():
    parser = argparse.ArgumentParser(description='Vacuum Cleaner Agent Runner')
    parser.add_argument('--agent-file', required=False,
                       help='Path to the Python file containing the agent class')
    parser.add_argument('--size', type=int, default=8, 
                       help='Environment size (creates size x size grid)')
    parser.add_argument('--dirt-rate', type=float, default=0.3, 
                       help='Percentage of cells that are dirty (0.0-1.0)')
    parser.add_argument('--server-url', default='http://localhost:5000',
                       help='Environment server URL')
    parser.add_argument('--verbose', action='store_true', default=False,
                       help='Print detailed output')
    
    # BaseAgent UI, recording y replay parameters
    parser.add_argument('--ui', '--enable-ui', action='store_true', default=False,
                       help='Enable pygame UI visualization')
    parser.add_argument('--record', '--record-game', action='store_true', default=False,
                       help='Record game session to JSON file')
    parser.add_argument('--replay', type=str, default=None,
                       help='Replay game from JSON file')
    parser.add_argument('--cell-size', type=int, default=60,
                       help='UI cell size in pixels (default: 60)')
    parser.add_argument('--fps', type=int, default=10,
                       help='UI frames per second (default: 10)')
    parser.add_argument('--no-auto-exit', action='store_true', default=False,
                       help='Disable auto-exit when simulation finishes (UI stays open)')
    parser.add_argument('--live-stats', action='store_true', default=False,
                       help='Show real-time statistics during simulation (pretty status bar)')
    parser.add_argument('--seed', type=int, default=None,
                       help='Random seed for reproducible simulations')
    
    args = parser.parse_args()
    
    # Validate arguments
    if not args.agent_file and not args.replay:
        parser.error("--agent-file is required when not using --replay mode")
    
    print("Vacuum Cleaner Agent Runner")
    print("Based on Russell & Norvig's AI textbook")
    print(f"Server: {args.server_url}")
    print(f"Agent file: {args.agent_file if args.agent_file else 'Not needed (replay mode)'}")
    print("="*50)
    
    # Load agent class from file or use replay agent
    if args.replay and not args.agent_file:
        agent_class = ReplayAgent
        print("Using ReplayAgent for replay mode")
    else:
        try:
            agent_class = load_agent_from_file(args.agent_file)
            print(f"Loaded agent class: {agent_class.__name__}")
        except Exception as e:
            print(f"Error loading agent from {args.agent_file}: {e}")
            return
    
    print("Make sure the environment server is running!")
    print()
    
    if args.replay:
        print(f"Replay mode: {args.replay}")
        if args.ui:
            print("UI enabled for replay visualization")
    
    # Run the single agent
    result = run_single_agent(agent_class, args.server_url, 
                            args.size, args.size, args.dirt_rate, 
                            args.verbose, 0, args.ui, args.record,
                            args.replay, args.cell_size, args.fps,
                            not args.no_auto_exit, args.live_stats, args.seed)
    
    if result['success']:
        print(f"Simulation completed successfully!")
        print(f"Final performance: {result['performance']}")
        if args.record and not args.replay:
            print("Game recording saved to game_data/ directory")
    else:
        print(f"Simulation failed: {result['error']}")

if __name__ == "__main__":
    main()
