import sys
import os
import random
from typing import Optional
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base_agent import BaseAgent

class ReflexAgent(BaseAgent):

    
    def __init__(self, server_url: str = "http://localhost:5000", 
                 enable_ui: bool = False,
                 record_game: bool = False, 
                 replay_file: Optional[str] = None,
                 cell_size: int = 60,
                 fps: int = 10,
                 auto_exit_on_finish: bool = True,
                 live_stats: bool = False):
        super().__init__(server_url, "ReflexAgent", enable_ui, record_game, 
                        replay_file, cell_size, fps, auto_exit_on_finish, live_stats)
        
        # Estado interno para movimiento circular
        self.movement_sequence = [self.up, self.right, self.down, self.left]
        self.current_move_index = 0
        # Estado interno para detectar paredes
        self.last_position= None
    
    def get_strategy_description(self) -> str:
        return "Limpia si está sucio y cambia de dirección, cambia de dirección si encuentra una pared"

    def think(self) -> bool:
        if not self.is_connected():
            return False

        perception = self.get_perception()
        if not perception or perception.get('is_finished', True):
            return False

        # Limpiar si hay suciedad
        if perception.get('is_dirty', False):
            current_direction = random.choice(self.movement_sequence)
            self.current_move_index=self.movement_sequence.index(current_direction)
            return self.suck()

        x, y = perception.get('position', (0, 0))

        # Inicializar last_position en el primer paso, sin cambiar dirección
        if not hasattr(self, 'last_position'):
            self.last_position = (x, y)
            # Solo devolver un movimiento aleatorio la primera vez
            return random.choice([self.up, self.down, self.left, self.right])


        # Si no se movió, cambiar dirección
        if (x, y) == self.last_position:
            possible_directions = [d for d in self.movement_sequence
                                if d != self.movement_sequence[self.current_move_index]]
            current_direction = random.choice(possible_directions)
            self.current_move_index=self.movement_sequence.index(current_direction)

        # Guardar posición actual para la próxima iteración
        self.last_position = (x, y)
        move_function=self.movement_sequence[self.current_move_index]
        # Avanzar en la dirección actual
        success=move_function()
        return success
    

def run_reflex_agent_simulation(size_x: int = 8, size_y: int = 8, 
                                dirt_rate: float = 0.3, 
                                server_url: str = "http://localhost:5000",
                                verbose: bool = True) -> int:
    """
    Función de conveniencia para ejecutar una simulación con ExampleAgent.
    """
    agent = ReflexAgent(server_url)
    
    try:
        if not agent.connect_to_environment(size_x, size_y, dirt_rate):
            return 0
        
        performance = agent.run_simulation(verbose)
        return performance
    
    finally:
        agent.disconnect()

if __name__ == "__main__":
    print("Reflex Agent - Circular Movement Pattern")
    print("Make sure the environment server is running on localhost:5000")
    print("Strategy: Clean if dirty, change directions when encountering a wall or after cleaning")
    print()
    
    performance = run_reflex_agent_simulation(verbose=True)
    print(f"\nFinal performance: {performance}")
    '''
    print("\nTo create your own agent:")
    print("1. Copy this file and rename it")
    print("2. Change the class name")  
    print("3. Implement your logic in the think() method")
    print("4. Register it in run_agent.py AVAILABLE_AGENTS dictionary")
    '''