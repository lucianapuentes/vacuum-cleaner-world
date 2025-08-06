# Game Data Directory

This directory contains recorded game sessions from vacuum cleaner agent simulations.

## File Format

Game recordings are saved in JSON format with the following structure:

```json
{
  "metadata": {
    "agent_type": "ReflexAgent",
    "environment_size": [8, 8],
    "dirt_rate": 0.3,
    "timestamp": "2024-01-01T10:00:00Z",
    "final_performance": 45,
    "total_actions": 150,
    "server_url": "http://localhost:5000",
    "environment_id": "uuid-string"
  },
  "initial_state": {
    "grid": [[0,1,0,1], [1,0,0,1], ...],
    "agent_position": [4, 4]
  },
  "steps": [
    {
      "step": 1,
      "action": "suck",
      "before_state": {
        "grid": [[0,1,0,1], ...],
        "agent_position": [4, 4],
        "is_dirty": true,
        "performance": 0
      },
      "after_state": {
        "grid": [[0,0,0,1], ...],
        "agent_position": [4, 4], 
        "is_dirty": false,
        "performance": 1
      },
      "reward": 1,
      "perception": {
        "position": [4, 4],
        "is_dirty": true,
        "actions_remaining": 999
      }
    }
  ]
}
```

## File Naming Convention

- `game_YYYY-MM-DD_HH-MM-SS_agenttype.json`
- Example: `game_2024-01-15_14-30-45_reflex.json`

## Usage

### Recording a Game
```bash
python run_agent.py --agent-type reflex --record --size 8 --dirt-rate 0.3
```

### Replaying a Game  
```bash
python run_agent.py --replay game_data/game_2024-01-15_14-30-45_reflex.json --ui
```

### Comparing Replay vs New Run
```bash
python run_agent.py --replay game_data/game_2024-01-15_14-30-45_reflex.json --compare --agent-type reflex --ui
```