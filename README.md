# Vacuum Cleaner AI - Student Guide

A Python simulation environment for creating AI agents that clean rooms, based on Russell & Norvig's AI textbook.

## Quick Start

### 1. Install Requirements
```bash
pip install -r requirements.txt
```

### 2. Start the Environment Server
```bash
python3 environment_server.py
```

### 3. Test with an Example Agent
```bash
python3 run_agent.py --agent-file agents/example_agent.py --ui
```

## Creating Your Agent

### Basic Template
Create your agent file in `student_agents/` directory:

```python
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base_agent import BaseAgent

class YourNameAgent(BaseAgent):
    def __init__(self, server_url="http://localhost:5000", **kwargs):
        super().__init__(server_url, "YourNameAgent", **kwargs)
    
    def get_strategy_description(self):
        return "Describe your cleaning strategy"
    
    def think(self):
        if not self.is_connected():
            return False
        
        perception = self.get_perception()
        if not perception or perception.get('is_finished', True):
            return False
        
        # Your logic here
        if perception.get('is_dirty', False):
            return self.suck()
        else:
            return self.up()  # or any movement
```

### Available Actions
- `self.up()` - Move up
- `self.down()` - Move down
- `self.left()` - Move left
- `self.right()` - Move right
- `self.suck()` - Clean dirt at current position
- `self.idle()` - Do nothing

### Getting Information

**Local Perception (Always Available):**
```python
perception = self.get_perception()
position = perception.get('position', (0, 0))
is_dirty = perception.get('is_dirty', False)
actions_remaining = perception.get('actions_remaining', 0)
```

**Global Environment (Use Carefully):**
```python
state = self.get_environment_state()
grid = state.get('grid', [])  # Shows all dirt locations
agent_pos = state.get('agent_position', [0, 0])
performance = state.get('performance', 0)
```

⚠️ **Note**: Global environment access may be restricted during evaluation.

## Testing Your Agent

### Basic Testing
```bash
# Test with UI visualization
python3 run_agent.py --agent-file student_agents/your_agent.py --ui

# Test with verbose output
python3 run_agent.py --agent-file student_agents/your_agent.py --verbose

# Test different environment sizes
python3 run_agent.py --agent-file student_agents/your_agent.py --size 10 --dirt-rate 0.5 --ui

# Test with reproducible results using a seed
python3 run_agent.py --agent-file student_agents/your_agent.py --seed 12345 --ui
```

### Recording and Replay
```bash
# Record your agent's performance
python3 run_agent.py --agent-file student_agents/your_agent.py --record --ui

# Replay a recorded session
python3 run_agent.py --replay game_data/your_recording.json --ui
```

## Example Agents

Study these example agents in the `agents/` folder:

- **`example_agent.py`** - Basic template with circular movement
- **`random_agent.py`** - Random movement strategy
- **`hybrid_agent.py`** - Combination of cleaning and random exploration
- **`reflex_agent.py`** - Systematic cleaning pattern

## Learning Resources

- **`USER_GUIDE.md`** - Comprehensive development guide
- **`README_ASSIGNMENT.md`** - Assignment-specific instructions
- **`API_DOCUMENTATION.md`** - Technical API reference

## Common Patterns

### Simple Reflex Agent
```python
def think(self):
    perception = self.get_perception()
    
    if perception.get('is_dirty', False):
        return self.suck()
    else:
        return self.up()
```

### Memory-Based Agent
```python
def __init__(self, **kwargs):
    super().__init__(**kwargs)
    self.visited = set()

def think(self):
    perception = self.get_perception()
    current_pos = perception.get('position', (0, 0))
    self.visited.add(current_pos)
    
    if perception.get('is_dirty', False):
        return self.suck()
    
    # Use memory to guide exploration
    # Your exploration logic here
    return self.right()
```

## Debugging Tips

1. **Use `--verbose`** to see what actions your agent takes
2. **Use `--ui`** to visualize your agent's movement
3. **Add print statements** to understand decision-making
4. **Test different environments** with `--size` and `--dirt-rate`
5. **Record sessions** to analyze behavior later
6. **Use `--seed`** for reproducible testing with identical environments

## File Structure

```
cleaner-world/
├── README.md                  # This guide
├── README_ASSIGNMENT.md       # Assignment instructions
├── USER_GUIDE.md             # Comprehensive guide
├── run_agent.py              # Main testing tool
├── base_agent.py             # Base class for all agents
├── environment_server.py     # Environment simulator
├── agents/                   # Example agents to study
│   ├── example_agent.py
│   ├── random_agent.py
│   └── hybrid_agent.py
├── student_agents/           # Your agents go here
└── game_data/               # Recorded sessions
```

## Assignment Submission

1. **File Naming**: `student_firstname_lastname_agent.py`
2. **Location**: Place in `student_agents/` directory
3. **Testing**: Thoroughly test before submission
4. **Documentation**: Include clear strategy description

## Competition Notice

Your instructor may evaluate agents in "competition mode" which simulates realistic robot constraints by limiting access to global information. Design agents that work well with local perception for best results.

## Getting Help

- Check the `USER_GUIDE.md` for detailed explanations
- Study example agents in the `agents/` folder
- Use `--verbose` and `--ui` flags for debugging
- Test with different environment configurations

Good luck with your AI agent!