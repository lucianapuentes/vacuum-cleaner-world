from abc import ABC, abstractmethod
import json
import os
import time
from datetime import datetime
from typing import Optional, Dict, List, Any
import pygame
import sys

from api_client import VacuumEnvironmentClient

class BaseAgent(ABC):
    """
    Clase base abstracta para todos los agentes que se conectan al servidor de entornos.
    
    Funcionalidades integradas:
    - Conexión/desconexión del servidor REST
    - Comunicación HTTP con la API REST
    - UI pygame integrada (opcional)
    - Sistema de grabación completa del juego
    - Sistema de replay de simulaciones grabadas
    - Métodos de acción básicos
    - Ciclo de simulación común
    
    Los agentes específicos solo deben implementar el método think().
    """
    
    def __init__(self, server_url: str = "http://localhost:5000", 
                 agent_name: str = "BaseAgent",
                 enable_ui: bool = False,
                 record_game: bool = False, 
                 replay_file: Optional[str] = None,
                 cell_size: int = 60,
                 fps: int = 10,
                 auto_exit_on_finish: bool = True,
                 live_stats: bool = False):
        """
        Inicializa el agente base con todas las funcionalidades.
        
        Args:
            server_url: URL del servidor de entornos
            agent_name: Nombre del agente
            enable_ui: Si activar la UI pygame
            record_game: Si grabar la simulación completa
            replay_file: Archivo de replay a reproducir (None para simulación normal)
            cell_size: Tamaño de cada celda en pixels (para UI)
            fps: Frames per second para la UI
            auto_exit_on_finish: Si cerrar automáticamente cuando termine la simulación
            live_stats: Si mostrar estadísticas en tiempo real durante la simulación
        """
        self.server_url = server_url
        self.agent_name = agent_name
        self.enable_ui = enable_ui
        self.record_game = record_game
        self.replay_file = replay_file
        self.cell_size = cell_size
        self.fps = fps
        self.auto_exit_on_finish = auto_exit_on_finish
        self.live_stats = live_stats
        
        # Cliente API REST
        self.client = VacuumEnvironmentClient(server_url)
        self.env_id = None
        self.connected = False
        
        # Estadísticas de la simulación
        self.total_actions = 0
        self.successful_actions = 0
        self.final_performance = 0
        
        # Estadísticas avanzadas para live stats
        self.visited_positions = set()
        self.action_counts = {
            'up': 0, 'down': 0, 'left': 0, 'right': 0, 
            'suck': 0, 'idle': 0
        }
        self.total_distance = 0
        self.last_position = None
        self.environment_size = (0, 0)
        self.initial_dirty_count = 0
        
        # Estadísticas de eficiencia para leaderboard
        self.suck_attempts = 0          # Total SUCK actions attempted
        self.successful_sucks = 0       # SUCK actions that actually cleaned dirt
        self.movement_actions = 0       # Total movement actions (up/down/left/right)
        self.idle_actions = 0          # Total IDLE actions
        self.total_dirt_available = 0   # Total dirt in environment at start
        
        # Sistema de grabación
        self.game_recording = {
            'metadata': {},
            'initial_state': {},
            'steps': []
        }
        
        # Sistema de replay
        self.replay_data = None
        self.replay_step = 0
        
        # UI pygame components
        self.screen = None
        self.clock = None
        self.font = None
        self.big_font = None
        self.running = True
        self.paused = False
        self.speed = fps
        self.animation_offset = 0
        self.cleaning_effect = None
        self.cleaning_timer = 0
        self.finish_time = None
        self.exit_delay = 3.0  # seconds to show final results before auto-exit
        
        # Colores para la UI
        self.colors = {
            'clean': (248, 248, 255),
            'clean_border': (220, 220, 235),
            'dirty_base': (101, 67, 33),
            'dirty_spots': (139, 69, 19),
            'agent_body': (70, 130, 180),
            'agent_accent': (100, 149, 237),
            'agent_wheel': (105, 105, 105),
            'grid': (200, 200, 210),
            'background': (245, 245, 250),
            'text': (40, 40, 40),
            'score': (34, 139, 34),
            'warning': (220, 20, 60),
            'disconnected': (255, 0, 0)
        }
        
        # Cargar datos de replay si se especifica
        if self.replay_file:
            self._load_replay_data()
    
    def connect_to_environment(self, sizeX: int = 8, sizeY: int = 8, 
                             dirt_rate: float = 0.3, 
                             start_x: int = None, start_y: int = None,
                             seed: int = None) -> bool:
        """
        Conecta el agente a un nuevo entorno en el servidor.
        """
        if self.replay_file:
            print(f"[{self.agent_name}] Using replay mode, skipping server connection")
            return True
        
        if not self.client.wait_for_server():
            print(f"[{self.agent_name}] Could not connect to environment server at {self.server_url}")
            return False
        
        self.env_id = self.client.create_environment(sizeX, sizeY, 
                                                   start_x, start_y, 
                                                   dirt_rate, seed)
        if not self.env_id:
            print(f"[{self.agent_name}] Failed to create environment")
            return False
        
        self.connected = True
        print(f"[{self.agent_name}] Connected to environment {self.env_id}")
        print(f"[{self.agent_name}] Environment: {sizeX}x{sizeY}, dirt rate: {dirt_rate}")
        
        # Inicializar estadísticas de eficiencia
        self._initialize_efficiency_stats()
        
        # Inicializar grabación si está habilitada
        if self.record_game:
            self._initialize_recording(sizeX, sizeY, dirt_rate)
        
        # Inicializar UI si está habilitada
        if self.enable_ui:
            self._initialize_ui(sizeX, sizeY)
        
        # Inicializar estadísticas avanzadas
        if self.live_stats:
            self._initialize_live_stats(sizeX, sizeY)
        
        return True
    
    def disconnect(self):
        """
        Desconecta el agente del servidor y limpia recursos.
        """
        if self.env_id and self.connected:
            self.client.delete_environment(self.env_id)
            print(f"[{self.agent_name}] Disconnected from environment {self.env_id}")
            self.env_id = None
            self.connected = False
        
        # Finalizar grabación si está activa
        if self.record_game and self.game_recording['steps']:
            self._save_recording()
        
        # Cerrar pygame si está activo
        if self.enable_ui and pygame.get_init():
            pygame.quit()
    
    def is_connected(self) -> bool:
        """
        Verifica si el agente está conectado (o en modo replay).
        """
        return self.connected or self.replay_file is not None
    
    # ============================================================================
    # MÉTODOS DE ACCIÓN BÁSICOS
    # ============================================================================
    
    def up(self) -> bool:
        """Mueve el agente hacia arriba."""
        return self._execute_action('up')
    
    def down(self) -> bool:
        """Mueve el agente hacia abajo."""
        return self._execute_action('down')
    
    def left(self) -> bool:
        """Mueve el agente hacia la izquierda."""
        return self._execute_action('left')
    
    def right(self) -> bool:
        """Mueve el agente hacia la derecha."""
        return self._execute_action('right')
    
    def suck(self) -> bool:
        """Limpia la suciedad en la posición actual."""
        return self._execute_action('suck')
    
    def idle(self) -> bool:
        """No hace nada (consume una acción)."""
        return self._execute_action('idle')
    
    def _execute_action(self, action: str) -> bool:
        """
        Ejecuta una acción y actualiza grabación si está activa.
        """
        if not self.is_connected():
            return False
        
        # En modo replay, no ejecutamos acciones reales
        if self.replay_file:
            return True
        
        # Capturar estado antes de la acción (para grabación)
        before_state = None
        if self.record_game:
            before_state = self._capture_current_state()
        
        # Actualizar estadísticas antes de la acción
        if self.live_stats:
            self._update_pre_action_stats(action)
        
        self.total_actions += 1
        result = self.client.execute_action(self.env_id, action)
        
        success = result and result.get('success', False)
        reward = result.get('reward', 0) if result else 0
        
        if success:
            self.successful_actions += 1
        
        # Actualizar estadísticas de eficiencia
        self._update_efficiency_stats(action, success, reward)
        
        # Actualizar estadísticas después de la acción
        if self.live_stats:
            self._update_post_action_stats(action, success)
        
        # Grabar paso si está habilitado
        if self.record_game and before_state:
            after_state = self._capture_current_state()
            self._record_step(action, before_state, after_state, result)
        
        return success
    
    def _initialize_efficiency_stats(self):
        """
        Inicializa las estadísticas de eficiencia capturando el estado inicial del entorno.
        """
        state = self.get_environment_state()
        if state and 'grid' in state:
            # Contar el total de suciedad disponible en el entorno
            grid = state['grid']
            self.total_dirt_available = sum(sum(row) for row in grid)
            print(f"[{self.agent_name}] Total dirt available: {self.total_dirt_available}")
    
    def _update_efficiency_stats(self, action: str, success: bool, reward: int):
        """
        Actualiza las estadísticas de eficiencia para el sistema de leaderboard.
        """
        if action == 'suck':
            self.suck_attempts += 1
            if reward > 0:  # Actually cleaned dirt
                self.successful_sucks += 1
        elif action in ['up', 'down', 'left', 'right']:
            self.movement_actions += 1
        elif action == 'idle':
            self.idle_actions += 1
    
    def get_perception(self) -> dict:
        """
        Obtiene la percepción actual del agente.
        """
        if not self.is_connected():
            return {}
        
        # En modo replay, usar datos del replay
        if self.replay_file:
            return self._get_replay_perception()
        
        perception = self.client.sense(self.env_id)
        if perception:
            return {
                'position': tuple(perception['position']),
                'is_dirty': perception['is_dirty'],
                'actions_remaining': perception['actions_remaining'],
                'is_finished': perception['is_finished']
            }
        return {}
    
    def get_environment_state(self) -> dict:
        """
        Obtiene el estado completo del entorno.
        """
        if not self.is_connected():
            return {}
        
        # En modo replay, usar datos del replay
        if self.replay_file:
            return self._get_replay_state()
        
        return self.client.get_state(self.env_id) or {}
    
    # ============================================================================
    # MÉTODO ABSTRACTO - DEBE SER IMPLEMENTADO POR AGENTES ESPECÍFICOS
    # ============================================================================
    
    @abstractmethod
    def think(self) -> bool:
        """
        Método abstracto que implementa la lógica de decisión del agente.
        
        Cada agente específico debe implementar este método con su propia
        estrategia de comportamiento.
        
        Returns:
            True si se ejecutó una acción, False si el agente debe terminar
        """
        pass
    
    # ============================================================================
    # SIMULACIÓN PRINCIPAL
    # ============================================================================
    
    def run_simulation(self, verbose: bool = False) -> int:
        """
        Ejecuta una simulación completa con el agente.
        
        Determina automáticamente el modo según la configuración:
        - Replay si replay_file está especificado
        - UI si enable_ui está activado
        - Headless en caso contrario
        """
        if self.replay_file:
            return self._run_replay(verbose)
        elif self.enable_ui:
            return self._run_with_ui(verbose)
        else:
            return self._run_headless(verbose)
    
    def _run_headless(self, verbose: bool = False) -> int:
        """
        Ejecuta simulación sin UI.
        """
        if not self.is_connected():
            print(f"[{self.agent_name}] Not connected to environment")
            return 0
        
        if verbose:
            print(f"[{self.agent_name}] Starting headless simulation...")
            print(f"[{self.agent_name}] Strategy: {self.get_strategy_description()}")
        
        while True:
            state = self.get_environment_state()
            if not state or state.get('is_finished', True):
                break
            
            # Mostrar estadísticas en tiempo real o verbose clásico
            if self.live_stats:
                self._display_live_stats(state)
            elif verbose and state.get('actions_taken', 0) % 100 == 0:
                pos = state.get('agent_position', [0, 0])
                print(f"[{self.agent_name}] Actions: {state.get('actions_taken', 0)}, "
                      f"Performance: {state.get('performance', 0)}, "
                      f"Position: ({pos[0]}, {pos[1]})")
            
            if not self.think():
                break
        
        final_state = self.get_environment_state()
        final_performance = final_state.get('performance', 0) if final_state else 0
        self.final_performance = final_performance
        
        if self.live_stats:
            # Nueva línea final para las live stats
            print()
            print(f"[{self.agent_name}] ✅ Simulation completed!")
            self._print_live_final_stats(final_performance)
        elif verbose:
            print(f"[{self.agent_name}] Simulation completed!")
            print(f"[{self.agent_name}] Final performance: {final_performance}")
            self._print_statistics()
        
        return final_performance
    
    def _run_with_ui(self, verbose: bool = False) -> int:
        """
        Ejecuta simulación con UI pygame.
        """
        if not self.is_connected():
            print(f"[{self.agent_name}] Not connected to environment")
            return 0
        
        if verbose:
            print(f"[{self.agent_name}] Starting UI simulation...")
            print(f"[{self.agent_name}] Strategy: {self.get_strategy_description()}")
            print(f"[{self.agent_name}] Controls: SPACE=pause, R=reset, +/-=speed, ESC=exit")
        
        last_performance = 0
        
        while self.running:
            self._handle_ui_events()
            
            if not self.paused:
                state = self.get_environment_state()
                if state and not state.get('is_finished', True):
                    current_performance = state.get('performance', 0)
                    if self.live_stats and state:
                            self._display_live_stats(state)
                    if self.think():
                        new_state = self.get_environment_state()
                        if new_state:
                            new_performance = new_state.get('performance', 0)
                            if new_performance > current_performance:
                                agent_pos = new_state.get('agent_position', [0, 0])
                                self.cleaning_effect = (agent_pos[0], agent_pos[1])
                                self.cleaning_timer = 0
                            
                            last_performance = new_performance
                            self.final_performance = new_performance
                else:
                    # Simulación terminada
                    if not self.paused:
                        self.paused = True
                        self.finish_time = time.time() if self.auto_exit_on_finish else None
                        # Store final performance when simulation ends
                        self.final_performance = last_performance
                        if verbose:
                            print(f"[{self.agent_name}] Simulation completed!")
                            if self.auto_exit_on_finish:
                                print(f"[{self.agent_name}] Auto-exiting in {self.exit_delay} seconds...")
            
            # Auto-exit después del delay si está habilitado
            if self.finish_time and time.time() - self.finish_time > self.exit_delay:
                if verbose:
                    print(f"[{self.agent_name}] Auto-exiting...")
                self.running = False
            
            self._update_ui_effects()
            self._draw_ui()
            
            pygame.display.flip()
            self.clock.tick(self.speed)
        
        if verbose:
            print(f"[{self.agent_name}] Final performance: {last_performance}")
            self._print_statistics()
        
        return last_performance
    
    def _run_replay(self, verbose: bool = False) -> int:
        """
        Reproduce una simulación grabada.
        """
        if not self.replay_data:
            print(f"[{self.agent_name}] No replay data loaded")
            return 0
        
        if verbose:
            print(f"[{self.agent_name}] Starting replay...")
            print(f"[{self.agent_name}] Original agent: {self.replay_data['metadata'].get('agent_type', 'Unknown')}")
            print(f"[{self.agent_name}] Total steps: {len(self.replay_data['steps'])}")
        
        if self.enable_ui:
            return self._run_replay_with_ui(verbose)
        else:
            return self._run_replay_headless(verbose)
    
    def _run_replay_headless(self, verbose: bool = False) -> int:
        """
        Reproduce simulación sin UI.
        """
        for step_data in self.replay_data['steps']:
            if verbose and step_data['step'] % 100 == 0:
                print(f"[{self.agent_name}] Replay step {step_data['step']}: "
                      f"Action={step_data['action']}, "
                      f"Performance={step_data['after_state']['performance']}")
        
        final_performance = self.replay_data['metadata'].get('final_performance', 0)
        
        if verbose:
            print(f"[{self.agent_name}] Replay completed!")
            print(f"[{self.agent_name}] Final performance: {final_performance}")
        
        return final_performance
    
    def _run_replay_with_ui(self, verbose: bool = False) -> int:
        """
        Reproduce simulación con UI.
        """
        # Inicializar UI para replay
        grid = self.replay_data['initial_state']['grid']
        size_y = len(grid)
        size_x = len(grid[0]) if size_y > 0 else 0
        self._initialize_ui(size_x, size_y)
        
        self.replay_step = 0
        
        while self.running and self.replay_step < len(self.replay_data['steps']):
            self._handle_ui_events()
            
            if not self.paused:
                step_data = self.replay_data['steps'][self.replay_step]
                
                # Simular efecto de limpieza si aplica
                if step_data['action'] == 'suck' and step_data.get('reward', 0) > 0:
                    pos = step_data['after_state']['agent_position']
                    self.cleaning_effect = (pos[0], pos[1])
                    self.cleaning_timer = 0
                
                self.replay_step += 1
                
                if verbose and self.replay_step % 100 == 0:
                    print(f"[{self.agent_name}] Replay step {self.replay_step}: "
                          f"Performance={step_data['after_state']['performance']}")
            
            self._update_ui_effects()
            self._draw_ui()
            
            pygame.display.flip()
            self.clock.tick(self.speed)
        
        # Manejar final del replay
        if self.replay_step >= len(self.replay_data['steps']):
            if not self.finish_time and self.auto_exit_on_finish:
                self.finish_time = time.time()
                if verbose:
                    print(f"[{self.agent_name}] Replay completed!")
                    print(f"[{self.agent_name}] Auto-exiting in {self.exit_delay} seconds...")
            elif not self.auto_exit_on_finish:
                self.paused = True
                if verbose:
                    print(f"[{self.agent_name}] Replay completed!")
        
        # Auto-exit después del delay si está habilitado
        if self.finish_time and time.time() - self.finish_time > self.exit_delay:
            if verbose:
                print(f"[{self.agent_name}] Auto-exiting...")
            self.running = False
        
        final_performance = self.replay_data['metadata'].get('final_performance', 0)
        
        if verbose and not self.auto_exit_on_finish:
            print(f"[{self.agent_name}] Final performance: {final_performance}")
        
        return final_performance
    
    # ============================================================================
    # SISTEMA DE GRABACIÓN
    # ============================================================================
    
    def _initialize_recording(self, sizeX: int, sizeY: int, dirt_rate: float):
        """
        Inicializa el sistema de grabación.
        """
        initial_state = self.get_environment_state()
        
        self.game_recording = {
            'metadata': {
                'agent_type': self.agent_name,
                'environment_size': [sizeX, sizeY],
                'dirt_rate': dirt_rate,
                'timestamp': datetime.now().isoformat(),
                'server_url': self.server_url,
                'environment_id': self.env_id
            },
            'initial_state': {
                'grid': initial_state.get('grid', []),
                'agent_position': initial_state.get('agent_position', [0, 0])
            },
            'steps': []
        }
    
    def _capture_current_state(self) -> dict:
        """
        Captura el estado actual del entorno.
        """
        state = self.get_environment_state()
        perception = self.get_perception()
        
        return {
            'grid': state.get('grid', []),
            'agent_position': state.get('agent_position', [0, 0]),
            'is_dirty': perception.get('is_dirty', False),
            'performance': state.get('performance', 0),
            'actions_taken': state.get('actions_taken', 0),
            'actions_remaining': perception.get('actions_remaining', 0)
        }
    
    def _record_step(self, action: str, before_state: dict, after_state: dict, result: dict):
        """
        Graba un paso de la simulación.
        """
        step_data = {
            'step': len(self.game_recording['steps']) + 1,
            'action': action,
            'before_state': before_state,
            'after_state': after_state,
            'reward': after_state['performance'] - before_state['performance'],
            'perception': {
                'position': before_state['agent_position'],
                'is_dirty': before_state['is_dirty'],
                'actions_remaining': before_state['actions_remaining']
            }
        }
        
        self.game_recording['steps'].append(step_data)
    
    def _save_recording(self):
        """
        Guarda la grabación en un archivo JSON.
        """
        # Actualizar metadata final
        self.game_recording['metadata'].update({
            'final_performance': self.final_performance,
            'total_actions': self.total_actions,
            'successful_actions': self.successful_actions
        })
        
        # Generar nombre de archivo
        timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
        filename = f"game_{timestamp}_{self.agent_name.lower()}.json"
        filepath = os.path.join("game_data", filename)
        
        # Guardar archivo
        try:
            with open(filepath, 'w') as f:
                json.dump(self.game_recording, f, indent=2)
            print(f"[{self.agent_name}] Game recording saved to {filepath}")
        except Exception as e:
            print(f"[{self.agent_name}] Error saving recording: {e}")
    
    # ============================================================================
    # SISTEMA DE REPLAY
    # ============================================================================
    
    def _load_replay_data(self):
        """
        Carga datos de replay desde archivo.
        """
        try:
            with open(self.replay_file, 'r') as f:
                self.replay_data = json.load(f)
            print(f"[{self.agent_name}] Loaded replay data from {self.replay_file}")
        except Exception as e:
            print(f"[{self.agent_name}] Error loading replay file: {e}")
            self.replay_data = None
    
    def _get_replay_perception(self) -> dict:
        """
        Obtiene percepción del replay actual.
        """
        if not self.replay_data or self.replay_step >= len(self.replay_data['steps']):
            return {'is_finished': True}
        
        step_data = self.replay_data['steps'][self.replay_step]
        return step_data.get('perception', {})
    
    def _get_replay_state(self) -> dict:
        """
        Obtiene estado del replay actual.
        """
        if not self.replay_data or self.replay_step >= len(self.replay_data['steps']):
            return {'is_finished': True}
        
        step_data = self.replay_data['steps'][self.replay_step]
        return step_data.get('after_state', {})
    
    # ============================================================================
    # SISTEMA UI (PYGAME)
    # ============================================================================
    
    def _initialize_ui(self, sizeX: int, sizeY: int):
        """
        Inicializa la UI pygame.
        """
        pygame.init()
        
        # Calcular dimensiones con mínimos para mostrar texto correctamente
        grid_width = sizeX * self.cell_size
        grid_height = sizeY * self.cell_size
        
        # Asegurar ancho mínimo para mostrar texto y controles (600px mínimo)
        self.width = max(grid_width, 600)
        # Asegurar altura mínima para HUD (120px para HUD + grid height mínimo de 200px)
        self.height = max(grid_height + 120, 320)
        
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption(f"Vacuum Cleaner - {self.agent_name}")
        
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 24)
        self.big_font = pygame.font.Font(None, 36)
        
        print(f"[{self.agent_name}] UI initialized ({sizeX}x{sizeY}, display: {self.width}x{self.height})")
    
    def _handle_ui_events(self):
        """
        Maneja eventos de pygame.
        """
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                elif event.key == pygame.K_r:
                    self._reset_simulation()
                elif event.key == pygame.K_PLUS or event.key == pygame.K_EQUALS:
                    self.speed = min(60, self.speed + 5)
                elif event.key == pygame.K_MINUS:
                    self.speed = max(1, self.speed - 5)
                elif event.key == pygame.K_ESCAPE:
                    self.running = False
    
    def _reset_simulation(self):
        """
        Reinicia la simulación (solo en modo normal, no replay).
        """
        if not self.replay_file and self.env_id:
            print(f"[{self.agent_name}] Resetting simulation...")
            # Aquí podrías implementar lógica de reset
            # Por ahora solo pausamos
            self.paused = True
    
    def _update_ui_effects(self):
        """
        Actualiza efectos visuales de la UI.
        """
        if self.cleaning_effect:
            self.cleaning_timer += 1
            if self.cleaning_timer > 20:
                self.cleaning_effect = None
                self.cleaning_timer = 0
        
        self.animation_offset = (self.animation_offset + 1) % 360
    
    def _draw_ui(self):
        """
        Dibuja la UI completa.
        """
        self.screen.fill(self.colors['background'])
        self._draw_grid()
        self._draw_hud()
    
    def _draw_grid(self):
        """
        Dibuja la grilla del entorno.
        """
        state = self.get_environment_state()
        if not state:
            return
        
        grid = state.get('grid', [])
        agent_pos = state.get('agent_position', [0, 0])
        
        if not grid:
            return
        
        # Calcular offset para centrar la grilla en la ventana
        grid_width = len(grid[0]) * self.cell_size
        grid_height = len(grid) * self.cell_size
        offset_x = (self.width - grid_width) // 2
        offset_y = 10  # Un pequeño margen desde arriba
        
        for y in range(len(grid)):
            for x in range(len(grid[0])):
                cell_rect = pygame.Rect(offset_x + x * self.cell_size, 
                                      offset_y + y * self.cell_size, 
                                      self.cell_size, self.cell_size)
                
                # Dibujar celda
                if grid[y][x] == 1:
                    pygame.draw.rect(self.screen, self.colors['dirty_base'], cell_rect)
                    self._draw_dirt_particles(x, y, cell_rect)
                else:
                    pygame.draw.rect(self.screen, self.colors['clean'], cell_rect)
                    pygame.draw.rect(self.screen, self.colors['clean_border'], cell_rect, 2)
                
                # Dibujar agente
                if x == agent_pos[0] and y == agent_pos[1]:
                    if grid[y][x] == 1:
                        highlight_rect = cell_rect.inflate(-4, -4)
                        pygame.draw.rect(self.screen, (255, 255, 0, 100), highlight_rect)
                    self._draw_vacuum_cleaner(x, y, cell_rect)
                
                pygame.draw.rect(self.screen, self.colors['grid'], cell_rect, 1)
                
                # Efecto de limpieza
                if self.cleaning_effect and self.cleaning_effect == (x, y):
                    self._draw_cleaning_effect(cell_rect)
    
    def _draw_dirt_particles(self, x, y, cell_rect):
        """
        Dibuja partículas de suciedad.
        """
        center_x = cell_rect.centerx
        center_y = cell_rect.centery
        
        dirt_spots = [
            (center_x - 8, center_y - 5, 4),
            (center_x + 6, center_y - 8, 3),
            (center_x - 3, center_y + 7, 5),
            (center_x + 8, center_y + 4, 3),
            (center_x - 12, center_y + 2, 2),
            (center_x + 2, center_y - 12, 4)
        ]
        
        for spot_x, spot_y, radius in dirt_spots:
            if (spot_x >= cell_rect.left and spot_x <= cell_rect.right and 
                spot_y >= cell_rect.top and spot_y <= cell_rect.bottom):
                pygame.draw.circle(self.screen, self.colors['dirty_spots'], 
                                 (spot_x, spot_y), radius)
                pygame.draw.circle(self.screen, self.colors['dirty_base'], 
                                 (spot_x, spot_y), radius - 1)
    
    def _draw_vacuum_cleaner(self, x, y, cell_rect):
        """
        Dibuja la aspiradora.
        """
        center_x = cell_rect.centerx
        center_y = cell_rect.centery
        size = self.cell_size // 3
        
        # Cuerpo
        body_rect = pygame.Rect(center_x - size//2, center_y - size//2, size, size)
        pygame.draw.ellipse(self.screen, self.colors['agent_body'], body_rect)
        pygame.draw.ellipse(self.screen, self.colors['agent_accent'], body_rect, 3)
        
        # Ruedas
        wheel_radius = 4
        wheel_positions = [
            (center_x - size//3, center_y + size//3),
            (center_x + size//3, center_y + size//3)
        ]
        for wheel_x, wheel_y in wheel_positions:
            pygame.draw.circle(self.screen, self.colors['agent_wheel'], 
                             (wheel_x, wheel_y), wheel_radius)
        
        # Cepillo
        brush_width = size // 2
        brush_height = 6
        brush_rect = pygame.Rect(center_x - brush_width//2, 
                               center_y + size//3 - brush_height//2,
                               brush_width, brush_height)
        pygame.draw.rect(self.screen, self.colors['agent_wheel'], brush_rect)
        
        # Mango
        handle_start = (center_x, center_y - size//3)
        handle_end = (center_x, center_y - size//2 - 8)
        pygame.draw.line(self.screen, self.colors['agent_accent'], 
                        handle_start, handle_end, 3)
    
    def _draw_cleaning_effect(self, cell_rect):
        """
        Dibuja efecto de limpieza.
        """
        center_x = cell_rect.centerx
        center_y = cell_rect.centery
        
        # Destellos
        sparkle_positions = [
            (center_x - 15, center_y - 10),
            (center_x + 12, center_y - 15),
            (center_x - 8, center_y + 12),
            (center_x + 18, center_y + 8),
            (center_x - 20, center_y + 5),
            (center_x + 5, center_y - 18)
        ]
        
        for spark_x, spark_y in sparkle_positions:
            pygame.draw.circle(self.screen, (255, 255, 200), (spark_x, spark_y), 3)
            pygame.draw.circle(self.screen, (255, 255, 100), (spark_x, spark_y), 2)
        
        # Líneas de succión
        suction_lines = [
            ((center_x - 10, center_y - 5), (center_x, center_y)),
            ((center_x + 8, center_y - 8), (center_x, center_y)),
            ((center_x - 6, center_y + 10), (center_x, center_y)),
            ((center_x + 12, center_y + 6), (center_x, center_y))
        ]
        
        for start_pos, end_pos in suction_lines:
            pygame.draw.line(self.screen, (150, 150, 255), start_pos, end_pos, 2)
    
    def _draw_hud(self):
        """
        Dibuja el HUD con información de la simulación.
        """
        state = self.get_environment_state()
        if not state:
            error_text = "DISCONNECTED FROM SERVER"
            error_surface = self.big_font.render(error_text, True, self.colors['disconnected'])
            error_x = (self.width - error_surface.get_width()) // 2
            self.screen.blit(error_surface, (error_x, self.height // 2))
            return
        
        grid = state.get('grid', [])
        # Posicionar HUD debajo de la grilla centrada, con un poco de margen
        grid_height = len(grid) * self.cell_size if grid else 0
        hud_y = 10 + grid_height + 15  # 10 (offset_y) + grid_height + margin
        
        # Puntuación
        score_text = f"Score: {state.get('performance', 0)}"
        score_surface = self.big_font.render(score_text, True, self.colors['score'])
        self.screen.blit(score_surface, (15, hud_y))
        
        # Acciones
        actions_text = f"Actions: {state.get('actions_taken', 0)}/1000"
        actions_surface = self.font.render(actions_text, True, self.colors['text'])
        self.screen.blit(actions_surface, (15, hud_y + 35))
        
        # Acciones restantes
        remaining = state.get('actions_remaining', 0)
        remaining_text = f"Remaining: {remaining}"
        color = self.colors['warning'] if remaining < 100 else self.colors['text']
        remaining_surface = self.font.render(remaining_text, True, color)
        self.screen.blit(remaining_surface, (15, hud_y + 55))
        
        # Barra de progreso
        progress_bar_width = 200
        progress_bar_height = 10
        progress_bar_x = self.width - progress_bar_width - 15
        progress_bar_y = hud_y + 5
        
        progress_rect = pygame.Rect(progress_bar_x, progress_bar_y, progress_bar_width, progress_bar_height)
        pygame.draw.rect(self.screen, (200, 200, 200), progress_rect)
        
        actions_taken = state.get('actions_taken', 0)
        progress = actions_taken / 1000
        progress_fill_width = int(progress_bar_width * progress)
        if progress_fill_width > 0:
            fill_rect = pygame.Rect(progress_bar_x, progress_bar_y, progress_fill_width, progress_bar_height)
            fill_color = self.colors['warning'] if progress > 0.9 else self.colors['score']
            pygame.draw.rect(self.screen, fill_color, fill_rect)
        
        pygame.draw.rect(self.screen, self.colors['text'], progress_rect, 1)
        
        # Texto de progreso
        progress_text = f"Progress: {progress:.1%}"
        progress_surface = self.font.render(progress_text, True, self.colors['text'])
        self.screen.blit(progress_surface, (progress_bar_x, progress_bar_y - 20))
        
        # Estado de pausa y auto-exit
        if self.paused:
            if self.finish_time and self.auto_exit_on_finish:
                # Mostrar countdown de auto-exit
                remaining_time = self.exit_delay - (time.time() - self.finish_time)
                if remaining_time > 0:
                    pause_text = f"✅ SIMULATION COMPLETED - Auto-exiting in {remaining_time:.1f}s"
                else:
                    pause_text = "✅ SIMULATION COMPLETED - Exiting..."
            else:
                pause_text = "⏸ PAUSED - Press SPACE to continue"
            
            pause_surface = self.big_font.render(pause_text, True, self.colors['warning'])
            pause_x = (self.width - pause_surface.get_width()) // 2
            self.screen.blit(pause_surface, (pause_x, hud_y + 30))
        
        # Controles
        controls_text = "Controls: SPACE=Pause, R=Reset, +/-=Speed, ESC=Exit"
        controls_surface = self.font.render(controls_text, True, self.colors['text'])
        self.screen.blit(controls_surface, (15, hud_y + 80))
        
        # Modo de simulación
        mode_text = ""
        if self.replay_file:
            mode_text = f"REPLAY MODE - Step {self.replay_step}/{len(self.replay_data['steps']) if self.replay_data else 0}"
        elif self.record_game:
            mode_text = "RECORDING MODE"
        
        if mode_text:
            mode_surface = self.font.render(mode_text, True, self.colors['warning'])
            mode_x = self.width - mode_surface.get_width() - 15
            self.screen.blit(mode_surface, (mode_x, hud_y + 80))
    
    # ============================================================================
    # SISTEMA DE ESTADÍSTICAS EN TIEMPO REAL
    # ============================================================================
    
    def _initialize_live_stats(self, sizeX: int, sizeY: int):
        """
        Inicializa el sistema de estadísticas en tiempo real.
        """
        self.environment_size = (sizeX, sizeY)
        
        # Contar celdas sucias iniciales
        state = self.get_environment_state()
        if state and 'grid' in state:
            grid = state['grid']
            self.initial_dirty_count = sum(sum(row) for row in grid)
        
        # Añadir posición inicial
        if state and 'agent_position' in state:
            pos = tuple(state['agent_position'])
            self.visited_positions.add(pos)
            self.last_position = pos
    
    def _update_pre_action_stats(self, action: str):
        """
        Actualiza estadísticas antes de ejecutar una acción.
        """
        # Contar tipos de acción
        if action in self.action_counts:
            self.action_counts[action] += 1
    
    def _update_post_action_stats(self, action: str, success: bool):
        """
        Actualiza estadísticas después de ejecutar una acción.
        """
        if not success:
            return
        
        # Obtener nueva posición
        state = self.get_environment_state()
        if state and 'agent_position' in state:
            new_pos = tuple(state['agent_position'])
            self.visited_positions.add(new_pos)
            
            # Calcular distancia si es movimiento
            if self.last_position and action in ['up', 'down', 'left', 'right']:
                if new_pos != self.last_position:
                    # Distancia Manhattan
                    distance = abs(new_pos[0] - self.last_position[0]) + abs(new_pos[1] - self.last_position[1])
                    self.total_distance += distance
            
            self.last_position = new_pos
    
    def _display_live_stats(self, state: dict):
        """
        Muestra estadísticas en tiempo real en la misma línea.
        """
        import sys
        
        actions_taken = state.get('actions_taken', 0)
        performance = state.get('performance', 0)
        pos = state.get('agent_position', [0, 0])
        
        # Calcular métricas
        total_cells = self.environment_size[0] * self.environment_size[1]
        visited_count = len(self.visited_positions)
        coverage = (visited_count / total_cells * 100) if total_cells > 0 else 0
        efficiency = (performance / actions_taken * 100) if actions_taken > 0 else 0
        
        # Construir línea de estadísticas
        stats_line = (
            f"[{self.agent_name}] "
            f"🎯 Actions: {actions_taken}/1000 | "
            f"🧹 Cleaned: {performance} | "
            f"📍 Pos: ({pos[0]},{pos[1]}) | "
            f"🗺️ Visited: {visited_count} | "
            f"⚡ Efficiency: {efficiency:.1f}% | "
            f"🎆 Coverage: {coverage:.1f}%"
        )
        
        # Mostrar sin nueva línea
        sys.stdout.write(f"\r{stats_line}")
        sys.stdout.flush()
    
    def _print_live_final_stats(self, final_performance: int):
        """
        Imprime estadísticas finales detalladas para modo live stats.
        """
        total_cells = self.environment_size[0] * self.environment_size[1]
        visited_count = len(self.visited_positions)
        coverage = (visited_count / total_cells * 100) if total_cells > 0 else 0
        efficiency = (final_performance / self.total_actions * 100) if self.total_actions > 0 else 0
        completion = (final_performance / self.initial_dirty_count * 100) if self.initial_dirty_count > 0 else 0
        
        print(f"[{self.agent_name}] 🏆 FINAL STATISTICS:")
        print(f"[{self.agent_name}]   🎯 Total Actions: {self.total_actions}/1000")
        print(f"[{self.agent_name}]   🧹 Cells Cleaned: {final_performance}/{self.initial_dirty_count} ({completion:.1f}%)")
        print(f"[{self.agent_name}]   🗺️ Exploration: {visited_count}/{total_cells} cells ({coverage:.1f}% coverage)")
        print(f"[{self.agent_name}]   ⚡ Cleaning Efficiency: {efficiency:.1f}% (cleaned per action)")
        print(f"[{self.agent_name}]   🚶 Total Distance: {self.total_distance} steps")
        
        # Mostrar distribución de acciones
        total_tracked = sum(self.action_counts.values())
        if total_tracked > 0:
            print(f"[{self.agent_name}]   🎯 Action Breakdown:")
            for action, count in self.action_counts.items():
                if count > 0:
                    percentage = (count / total_tracked * 100)
                    emoji = {'up': '⬆️', 'down': '⬇️', 'left': '⬅️', 
                            'right': '➡️', 'suck': '🧹', 'idle': '⏸️'}.get(action, '🔄')
                    print(f"[{self.agent_name}]     {emoji} {action}: {count} ({percentage:.1f}%)")
    
    # ============================================================================
    # MÉTODOS DE UTILIDAD
    # ============================================================================
    
    def get_strategy_description(self) -> str:
        """
        Retorna una descripción de la estrategia del agente.
        Puede ser sobrescrito por agentes específicos.
        """
        return "Base agent strategy (not implemented)"
    
    def get_statistics(self) -> dict:
        """
        Retorna estadísticas de la simulación actual.
        """
        # Calcular métricas de eficiencia
        cleaning_efficiency = (self.successful_sucks / self.total_actions) if self.total_actions > 0 else 0
        movement_efficiency = (self.successful_sucks / self.movement_actions) if self.movement_actions > 0 else 0
        action_efficiency = (self.successful_sucks / self.suck_attempts) if self.suck_attempts > 0 else 0
        
        # Eficiencia general (considera tanto limpieza como cobertura)
        overall_efficiency = (self.successful_sucks / self.total_actions) * (self.successful_sucks / max(self.total_dirt_available, 1)) if self.total_actions > 0 else 0
        
        return {
            # Estadísticas básicas
            'agent_name': self.agent_name,
            'total_actions': self.total_actions,
            'successful_actions': self.successful_actions,
            'success_rate': (self.successful_actions / self.total_actions) if self.total_actions > 0 else 0,
            
            # Estadísticas de eficiencia para leaderboard
            'suck_attempts': self.suck_attempts,
            'successful_sucks': self.successful_sucks,
            'movement_actions': self.movement_actions,
            'idle_actions': self.idle_actions,
            'total_dirt_available': self.total_dirt_available,
            
            # Métricas de eficiencia calculadas
            'cleaning_efficiency': cleaning_efficiency,      # dirt_sucked / total_steps
            'movement_efficiency': movement_efficiency,      # dirt_sucked / movement_steps
            'action_efficiency': action_efficiency,          # dirt_sucked / suck_attempts
            'overall_efficiency': overall_efficiency,        # combined efficiency score
            
            # Metadatos del sistema
            'connected': self.connected,
            'env_id': self.env_id,
            'ui_enabled': self.enable_ui,
            'recording': self.record_game,
            'replay_mode': self.replay_file is not None
        }
    
    def _print_statistics(self):
        """
        Imprime estadísticas de la simulación.
        """
        print(f"[{self.agent_name}] Actions executed: {self.total_actions}")
        success_rate = (self.successful_actions/self.total_actions)*100 if self.total_actions > 0 else 0
        print(f"[{self.agent_name}] Success rate: {success_rate:.1f}%")
        
        if self.record_game and self.game_recording['steps']:
            print(f"[{self.agent_name}] Steps recorded: {len(self.game_recording['steps'])}")
    
    def __str__(self):
        return f"{self.agent_name}(connected={self.connected}, ui={self.enable_ui}, recording={self.record_game})"
    
    def __repr__(self):
        return self.__str__()
