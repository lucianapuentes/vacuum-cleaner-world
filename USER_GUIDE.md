# Vacuum Cleaner Agent Runner - User Guide

A Python-based simulation runner for vacuum cleaner agents based on Russell & Norvig's AI textbook.

## Overview

This tool allows you to run custom vacuum cleaner agents in a simulated environment. You provide a Python file containing your agent implementation, and the runner will execute it in the vacuum cleaner world.

## Requirements

- Python 3.x
- pygame (for UI visualization, optional)
- Running environment server (default: http://localhost:5000)

## Basic Usage

```bash
python3 run_agent.py --agent-file <path_to_your_agent.py> [options]
```

## Required Arguments

| Argument | Description |
|----------|-------------|
| `--agent-file` | Path to the Python file containing your agent class (required) |

## Environment Options

| Argument | Default | Description |
|----------|---------|-------------|
| `--size` | 8 | Environment size (creates size × size grid) |
| `--dirt-rate` | 0.3 | Percentage of cells that are dirty (0.0-1.0) |
| `--server-url` | http://localhost:5000 | Environment server URL |

## Output Options

| Argument | Description |
|----------|-------------|
| `--verbose` | Print detailed output during simulation |

## UI and Visualization

| Argument | Default | Description |
|----------|---------|-------------|
| `--ui` | false | Enable pygame UI visualization |
| `--cell-size` | 60 | UI cell size in pixels |
| `--fps` | 10 | UI frames per second |
| `--no-auto-exit` | false | Keep UI open after simulation finishes |
| `--live-stats` | false | Show real-time statistics during simulation |

## Recording and Replay

| Argument | Description |
|----------|-------------|
| `--record` | Record game session to JSON file |
| `--replay <file>` | Replay game from JSON file |

## Examples

### Basic Agent Execution
```bash
python3 run_agent.py --agent-file my_agent.py
```

### With Custom Environment
```bash
python3 run_agent.py --agent-file my_agent.py --size 10 --dirt-rate 0.5
```

### With UI Visualization
```bash
python3 run_agent.py --agent-file my_agent.py --ui --verbose
```

### Recording a Session
```bash
python3 run_agent.py --agent-file my_agent.py --record --ui
```

### Replaying a Session
```bash
python3 run_agent.py --agent-file my_agent.py --replay game_data/game_2024-01-01_12-00-00_myagent.json --ui
```

### Custom Server and Environment
```bash
python3 run_agent.py --agent-file my_agent.py --server-url http://remote-server:8080 --size 12 --dirt-rate 0.4 --verbose
```

## Agent Implementation Requirements

Your agent file must contain a class that:

1. **Inherits from BaseAgent** (or implements the required interface)
2. **Implements the `think()` method** - This is where your agent logic goes
3. **Implements the `get_strategy_description()` method** - Returns a string describing your strategy

### Example Agent Structure

```python
from base_agent import BaseAgent

class MyAgent(BaseAgent):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # Your initialization code here
    
    def think(self):
        # Your agent logic here
        # Return True if action was successful, False to end simulation
        return self.suck()
    
    def get_strategy_description(self):
        return "My custom cleaning strategy"
```

## Creating a New Agent

This section provides a comprehensive guide for creating your own vacuum cleaner agent from scratch.

### Agent Requirements

Every agent must:

1. **Inherit from BaseAgent**: Import and extend the BaseAgent class
2. **Implement `think()` method**: Contains your agent's decision-making logic
3. **Implement `get_strategy_description()` method**: Returns a string describing your strategy
4. **Handle perceptions correctly**: Use the perception and environment state APIs properly

### Step-by-Step Creation Process

#### 1. Choose a Location
You can place your agent file in:
- `agents/` directory (for built-in agents)
- `student_agents/` directory (for student submissions)  
- Any custom directory or path

#### 2. Create the Python File
Create a new `.py` file with a descriptive name:
```bash
# Examples:
my_smart_agent.py
zigzag_cleaner_agent.py
random_walk_agent.py
```

#### 3. Basic Template Structure
```python
import sys
import os
# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base_agent import BaseAgent

class MySmartAgent(BaseAgent):
    """
    Brief description of your agent's strategy.
    """
    
    def __init__(self, server_url="http://localhost:5000", **kwargs):
        super().__init__(server_url, "MySmartAgent", **kwargs)
        
        # Initialize any state variables your agent needs
        self.visited_positions = set()
        self.current_target = None
    
    def get_strategy_description(self):
        return "Description of your cleaning strategy"
    
    def think(self):
        """
        Main decision-making method.
        
        Returns:
            bool: True if an action was performed, False to end simulation
        """
        if not self.is_connected():
            return False
        
        # Get current perception
        perception = self.get_perception()
        if not perception or perception.get('is_finished', True):
            return False
        
        # Your decision logic here
        if perception.get('is_dirty', False):
            return self.suck()
        else:
            return self.up()  # or whatever movement you want
```

### Core Implementation Details

#### The `think()` Method
This is where your agent's intelligence lives. The method should:

```python
def think(self):
    # 1. Check connection status
    if not self.is_connected():
        return False
    
    # 2. Get current perception
    perception = self.get_perception()
    if not perception or perception.get('is_finished', True):
        return False
    
    # 3. Make decisions based on perception
    current_pos = perception.get('position', (0, 0))
    is_dirty = perception.get('is_dirty', False)
    actions_remaining = perception.get('actions_remaining', 0)
    
    # 4. Execute an action and return success status
    if is_dirty:
        return self.suck()
    else:
        # Your movement logic
        return self.right()
```

#### Available Actions
Your agent can perform these actions:
- `self.up()` - Move up
- `self.down()` - Move down  
- `self.left()` - Move left
- `self.right()` - Move right
- `self.suck()` - Clean dirt at current position
- `self.idle()` - Do nothing (consumes an action)

#### Perception vs Environment State

Understanding the difference between local and global information is crucial for competition readiness:

**🔍 `get_perception()` - Local Information (Always Available)**
- Current position only
- Dirt status of current cell
- Actions remaining
- Simulation status
- **Competition Safe**: Always works in all modes

**🌍 `get_environment_state()` - Global Information (May Be Restricted)**
- Complete grid with all dirt locations
- Full performance metrics
- Agent position from external view  
- **Competition Warning**: May be limited during evaluation

```python
# ✅ LOCAL PERCEPTION - Always works, competition-safe
perception = self.get_perception()
pos = perception.get('position', (0, 0))
is_dirty = perception.get('is_dirty', False)
actions_left = perception.get('actions_remaining', 0)

# ⚠️ GLOBAL STATE - May be restricted in competition mode
state = self.get_environment_state()
full_grid = state.get('grid', [])        # 🚨 Shows ALL dirt locations
agent_pos = state.get('agent_position', [0, 0])  # 🚨 External position
performance = state.get('performance', 0)         # 🚨 Current score
```

**💡 Competition-Ready Strategy**: Use local perception as your primary information source, and global state only for initialization or boundary checking.

### Complete Working Example

Here's a fully functional agent that implements a systematic sweep pattern:

```python
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base_agent import BaseAgent

class SweepAgent(BaseAgent):
    """
    Systematic sweep agent that cleans in a zigzag pattern.
    """
    
    def __init__(self, server_url="http://localhost:5000", **kwargs):
        super().__init__(server_url, "SweepAgent", **kwargs)
        
        # Navigation state
        self.current_row = 0
        self.direction = 1  # 1 = right, -1 = left
        self.grid_size = None
        self.initialized = False
    
    def get_strategy_description(self):
        return "Systematic zigzag sweep pattern with immediate cleaning"
    
    def _initialize_grid_info(self):
        """Initialize grid dimensions on first call."""
        if self.initialized:
            return
        
        state = self.get_environment_state()
        if state and 'grid' in state:
            grid = state['grid']
            self.grid_size = (len(grid[0]) if grid else 0, len(grid))
            self.initialized = True
    
    def _get_next_sweep_position(self, current_pos):
        """Calculate next position in sweep pattern."""
        x, y = current_pos
        
        # Move horizontally in current direction
        next_x = x + self.direction
        
        # Check if we need to turn
        if next_x < 0 or next_x >= self.grid_size[0]:
            # Move to next row and reverse direction
            self.current_row += 1
            self.direction *= -1
            
            # Reset if we've swept everything
            if self.current_row >= self.grid_size[1]:
                self.current_row = 0
                self.direction = 1
                return (0, 0)
            
            return (0 if self.direction == 1 else self.grid_size[0] - 1, self.current_row)
        
        return (next_x, y)
    
    def think(self):
        if not self.is_connected():
            return False
        
        perception = self.get_perception()
        if not perception or perception.get('is_finished', True):
            return False
        
        # Initialize grid info if needed
        self._initialize_grid_info()
        if not self.initialized:
            return False
        
        current_pos = perception.get('position', (0, 0))
        
        # Rule 1: Clean if dirty
        if perception.get('is_dirty', False):
            return self.suck()
        
        # Rule 2: Move to next sweep position
        target_pos = self._get_next_sweep_position(current_pos)
        
        # Move towards target
        if current_pos[0] < target_pos[0]:
            return self.right()
        elif current_pos[0] > target_pos[0]:
            return self.left()
        elif current_pos[1] < target_pos[1]:
            return self.down()
        elif current_pos[1] > target_pos[1]:
            return self.up()
        else:
            # At target, continue sweep
            return self.idle()
```

### Testing Your Agent

#### Basic Testing
```bash
# Test with default settings
python3 run_agent.py --agent-file my_agent.py

# Test with custom environment
python3 run_agent.py --agent-file my_agent.py --size 10 --dirt-rate 0.4 --verbose

# Test with UI for visual debugging
python3 run_agent.py --agent-file my_agent.py --ui --verbose
```

#### Advanced Testing
```bash
# Record a session for analysis
python3 run_agent.py --agent-file my_agent.py --record --ui

# Test on different environment sizes
python3 run_agent.py --agent-file my_agent.py --size 4 --dirt-rate 0.1
python3 run_agent.py --agent-file my_agent.py --size 12 --dirt-rate 0.8
```

### Best Practices

1. **Keep State Simple**: Only track what you need for decision-making
2. **Handle Edge Cases**: Check for finished simulations and connection issues
3. **Use Meaningful Names**: Class names should describe the strategy
4. **Add Comments**: Document your decision logic clearly
5. **Test Incrementally**: Start simple, then add complexity
6. **Profile Performance**: Use `--verbose` to monitor your agent's behavior

### Troubleshooting

**"No valid agent class found"**
- Ensure your class inherits from BaseAgent
- Check that `think()` and `get_strategy_description()` methods exist
- Verify the class name doesn't conflict with existing classes

**Agent doesn't move as expected**
- Add `--verbose` flag to see what actions are being executed
- Use `--ui` flag to visually debug movement
- Check that `think()` returns `True` for successful actions

**Import errors**
- Ensure the sys.path.append line is correct for your file location
- Check that base_agent.py is accessible from your agent file location

**Performance issues**
- Avoid expensive computations in `think()`  
- Don't call `get_environment_state()` unless necessary
- Use `get_perception()` for local information

### Competition Mode and Fair Play

**Important for Students**: Your instructor may run evaluations in "competition mode" which restricts access to global environment information to simulate realistic robot constraints.

**What this means:**
- **Development**: You can use `get_environment_state()` for learning and debugging
- **Competition**: The instructor may restrict this access during grading
- **Fair Play**: Design agents that work well with local perception only

**Competition-Ready Design Tips:**
1. **Primary Strategy**: Use `get_perception()` for main decision-making
2. **Global Info as Helper**: Use `get_environment_state()` only for initialization or bounds checking  
3. **Memory and Learning**: Track visited positions and discovered patterns
4. **Efficient Exploration**: Develop smart exploration strategies without omniscience

**Example Competition-Ready Pattern:**
```python
def think(self):
    # ✅ ALWAYS works - competition safe
    perception = self.get_perception()
    
    if perception.get('is_dirty'):
        return self.suck()
    
    # ⚠️ Use global info sparingly - may be restricted in competition
    if not self.initialized:
        state = self.get_environment_state()  # One-time setup only
        self.grid_size = (len(state.get('grid', [[]])[0]), len(state.get('grid', [])))
        self.initialized = True
    
    # ✅ Make decisions based on local info and memory
    return self._explore_intelligently(perception)
```

**Why Competition Mode Exists:**
- **Real-world simulation**: Actual robots don't have omniscient sensors
- **Algorithm focus**: Emphasizes intelligent exploration over global optimization
- **Fair comparison**: All agents operate under same realistic constraints
- **Educational value**: Teaches practical AI problem-solving techniques

## Simulation Output

The runner will display:
- Agent class name loaded
- Simulation progress (if verbose)
- Final performance score
- Execution time
- Success/failure status

### Example Output
```
Vacuum Cleaner Agent Runner
Based on Russell & Norvig's AI textbook
Server: http://localhost:5000
Agent file: my_agent.py
==================================================
Loaded agent class: MyAgent
Make sure the environment server is running!

Simulation completed successfully!
Final performance: 85
```

## Troubleshooting

### Common Issues

**"Agent file not found"**
- Check that the file path is correct
- Use absolute paths if relative paths don't work

**"No valid agent class found"**
- Ensure your agent class implements `think()` and `get_strategy_description()`
- Make sure the class inherits from BaseAgent or implements the required interface

**"Failed to connect to environment"**
- Verify the environment server is running
- Check the server URL is correct
- Ensure the server is accessible from your machine

**UI doesn't appear**
- Make sure pygame is installed: `pip install pygame`
- Verify you're using the `--ui` flag

## Tips

1. **Start Simple**: Begin with the basic command and add options as needed
2. **Use Verbose Mode**: Add `--verbose` to see what your agent is doing
3. **Test with UI**: Use `--ui` to visually debug your agent's behavior
4. **Record Sessions**: Use `--record` to save interesting runs
5. **Experiment with Environment**: Try different `--size` and `--dirt-rate` values

## Getting Help

Use the built-in help to see all available options:
```bash
python3 run_agent.py --help
```
