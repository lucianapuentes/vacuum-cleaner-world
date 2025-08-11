import random
import numpy as np
from enum import Enum

class Action(Enum):
    UP = "up"
    DOWN = "down" 
    LEFT = "left"
    RIGHT = "right"
    SUCK = "suck"
    IDLE = "idle"

class Environment:
    def __init__(self, sizeX, sizeY, init_posX, init_posY, dirt_rate, seed=None):
        self.sizeX = sizeX
        self.sizeY = sizeY
        self.grid = np.zeros((sizeY, sizeX), dtype=int)
        self.agent_x = init_posX
        self.agent_y = init_posY
        self.dirt_rate = dirt_rate
        self.performance = 0
        self.actions_taken = 0
        self.max_actions = 1000
        self.completion_reason = None
        
        if seed is not None:
            random.seed(seed)
        
        self._initialize_dirt()
    
    def _initialize_dirt(self):
        total_cells = self.sizeX * self.sizeY
        num_dirty = int(total_cells * self.dirt_rate)
        
        dirty_positions = random.sample(
            [(x, y) for x in range(self.sizeX) for y in range(self.sizeY)],
            num_dirty
        )
        
        for x, y in dirty_positions:
            self.grid[y, x] = 1
    
    def accept_action(self, action):
        if self.actions_taken >= self.max_actions:
            return False
            
        self.actions_taken += 1
        
        if action == Action.UP:
            if self.agent_y > 0:
                self.agent_y -= 1
        elif action == Action.DOWN:
            if self.agent_y < self.sizeY - 1:
                self.agent_y += 1
        elif action == Action.LEFT:
            if self.agent_x > 0:
                self.agent_x -= 1
        elif action == Action.RIGHT:
            if self.agent_x < self.sizeX - 1:
                self.agent_x += 1
        elif action == Action.SUCK:
            if self.is_dirty():
                self.grid[self.agent_y, self.agent_x] = 0
                self.performance += 1
        elif action == Action.IDLE:
            pass
        
        return True
    
    def is_dirty(self):
        return self.grid[self.agent_y, self.agent_x] == 1
    
    def all_dirt_cleaned(self):
        """Check if all dirt has been cleaned from the environment."""
        return np.sum(self.grid) == 0
    
    def get_performance(self):
        return self.performance
    
    def get_agent_position(self):
        return self.agent_x, self.agent_y
    
    def is_finished(self):
        if self.actions_taken >= self.max_actions:
            if self.completion_reason is None:
                self.completion_reason = "max_steps_reached"
            return True
        if self.all_dirt_cleaned():
            if self.completion_reason is None:
                self.completion_reason = "all_cleaned"
            return True
        return False
    
    def get_actions_remaining(self):
        return self.max_actions - self.actions_taken
    
    def get_grid_copy(self):
        return self.grid.copy()
    
    def print_environment(self):
        print(f"Environment {self.sizeX}x{self.sizeY}")
        print(f"Agent position: ({self.agent_x}, {self.agent_y})")
        print(f"Performance: {self.performance}")
        print(f"Actions taken: {self.actions_taken}/{self.max_actions}")
        print("Grid (A=Agent, D=Dirt, C=Clean):")
        
        for y in range(self.sizeY):
            row = ""
            for x in range(self.sizeX):
                if x == self.agent_x and y == self.agent_y:
                    row += "A "
                elif self.grid[y, x] == 1:
                    row += "D "
                else:
                    row += "C "
            print(row)
        print()