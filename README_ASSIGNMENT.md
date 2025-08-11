# Student Assignment Guide: Vacuum Cleaner AI Agent

This guide provides the essential information needed to complete your vacuum cleaner AI agent assignment.

## Quick Start

### 1. Create Your Agent File
Create a file named `student_[firstname]_[lastname]_agent.py` in the `student_agents/` directory.

Example: `student_alice_chen_agent.py`

### 2. Basic Agent Template
```python
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from base_agent import BaseAgent

class YourNameAgent(BaseAgent):
    """
    Your vacuum cleaner agent implementation.
    """
    
    def __init__(self, server_url="http://localhost:5000", **kwargs):
        super().__init__(server_url, "YourNameAgent", **kwargs)
        # Add your initialization code here
    
    def get_strategy_description(self):
        return "Describe your cleaning strategy here"
    
    def think(self):
        """
        Your agent's decision-making logic goes here.
        Return True if an action was performed, False to end simulation.
        """
        if not self.is_connected():
            return False
        
        # Your code here
        # Return one of: self.up(), self.down(), self.left(), self.right(), self.suck(), self.idle()
        return self.idle()
```

### 3. Test Your Agent
```bash
python3 run_agent.py --agent-file student_agents/student_alice_chen_agent.py --ui
```

## Available Actions

Your agent can perform these actions:
- `self.up()` - Move up
- `self.down()` - Move down
- `self.left()` - Move left
- `self.right()` - Move right
- `self.suck()` - Clean dirt at current position
- `self.idle()` - Do nothing (still consumes an action)

## Information Sources

### Local Perception (Always Available)
```python
perception = self.get_perception()
position = perception.get('position', (0, 0))        # Current (x, y) position
is_dirty = perception.get('is_dirty', False)         # Is current cell dirty?
actions_remaining = perception.get('actions_remaining', 0)  # Actions left
is_finished = perception.get('is_finished', False)   # Is simulation done?
```

### Global Environment State (Use Carefully)
```python
state = self.get_environment_state()
grid = state.get('grid', [])                    # Complete grid (0=clean, 1=dirty)
agent_pos = state.get('agent_position', [0, 0]) # Agent position
performance = state.get('performance', 0)       # Current score
actions_taken = state.get('actions_taken', 0)   # Actions used so far
```

⚠️ **Important**: Global environment access may be restricted during evaluation to simulate realistic robot constraints. Design your agent to work primarily with local perception.


## Assignment Requirements

1. **File Naming**: Follow the exact naming pattern: `student_firstname_lastname_agent.py`
2. **Class Name**: Use a descriptive class name ending with "Agent"
3. **Required Methods**: Implement `think()` and `get_strategy_description()`
4. **Strategy Description**: Provide a clear explanation of your approach
5. **Functionality**: Your agent should clean dirt and explore the environment

## Testing Commands

```bash
# Basic test with UI
python3 run_agent.py --agent-file student_agents/student_your_name_agent.py --ui

# Test with different environment sizes
python3 run_agent.py --agent-file student_agents/student_your_name_agent.py --size 10 --dirt-rate 0.5 --ui

# Verbose output for debugging
python3 run_agent.py --agent-file student_agents/student_your_name_agent.py --verbose

# Record your session
python3 run_agent.py --agent-file student_agents/student_your_name_agent.py --record --ui
```
## Debugging Tips

1. **Use `--verbose` flag** to see what actions your agent is taking
2. **Use `--ui` flag** to visually debug movement patterns
3. **Check return values**: `think()` should return `True` for successful actions
4. **Add print statements** to understand your agent's decision-making
5. **Test with different environment sizes** and dirt rates

## Performance Metrics

Your agent will be evaluated on:
- **Performance Score**: Number of dirt cells cleaned
- **Actions taken**: Number of actions taken to clean all dirt cells
- **Efficiency**: How effectively you use your available actions
- **Strategy**: Quality of your exploration and cleaning approach

## Submission Guidelines

1. Ensure your agent file is in the `student_agents/` directory
2. Test your agent thoroughly before submission
3. Your agent should complete the simulation without errors
4. Include a clear strategy description in `get_strategy_description()`
5. Pull your submission to `vacuum-clearn-comp-2025` repository

## Competition Mode Notice

Your instructor may evaluate agents in "competition mode" which restricts access to global environment information. This simulates realistic robot constraints where you can only see your immediate surroundings. Design your agent to work well with local perception only for the best results.

Good luck with your assignment!
