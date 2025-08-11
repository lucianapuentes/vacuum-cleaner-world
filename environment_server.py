from flask import Flask, request, jsonify
from flask_cors import CORS
import uuid
import threading
import time
from environment import Environment, Action

app = Flask(__name__)
CORS(app)

environments = {}
environment_lock = threading.Lock()

class EnvironmentServer:
    def __init__(self):
        self.environments = {}
        self.lock = threading.Lock()
    
    def create_environment(self, sizeX, sizeY, init_posX, init_posY, dirt_rate, seed=None):
        env_id = str(uuid.uuid4())
        with self.lock:
            env = Environment(sizeX, sizeY, init_posX, init_posY, dirt_rate, seed)
            self.environments[env_id] = {
                'environment': env,
                'created_at': time.time(),
                'last_access': time.time()
            }
        return env_id
    
    def get_environment(self, env_id):
        with self.lock:
            if env_id in self.environments:
                self.environments[env_id]['last_access'] = time.time()
                return self.environments[env_id]['environment']
        return None
    
    def delete_environment(self, env_id):
        with self.lock:
            if env_id in self.environments:
                del self.environments[env_id]
                return True
        return False
    
    def cleanup_old_environments(self, max_age=3600):
        current_time = time.time()
        with self.lock:
            to_delete = []
            for env_id, env_data in self.environments.items():
                if current_time - env_data['last_access'] > max_age:
                    to_delete.append(env_id)
            
            for env_id in to_delete:
                del self.environments[env_id]
        
        return len(to_delete)

env_server = EnvironmentServer()

@app.route('/api/environment', methods=['POST'])
def create_environment():
    try:
        data = request.get_json()
        
        sizeX = data.get('sizeX', 8)
        sizeY = data.get('sizeY', 8)
        init_posX = data.get('init_posX', sizeX // 2)
        init_posY = data.get('init_posY', sizeY // 2)
        dirt_rate = data.get('dirt_rate', 0.3)
        seed = data.get('seed', None)
        
        if not (1 <= sizeX <= 256 and 1 <= sizeY <= 256):
            return jsonify({'error': 'Invalid size parameters'}), 400
        
        if not (0 <= init_posX < sizeX and 0 <= init_posY < sizeY):
            return jsonify({'error': 'Invalid initial position'}), 400
        
        if not (0.0 <= dirt_rate <= 1.0):
            return jsonify({'error': 'Invalid dirt rate'}), 400
        
        env_id = env_server.create_environment(sizeX, sizeY, init_posX, init_posY, dirt_rate, seed)
        
        return jsonify({
            'environment_id': env_id,
            'sizeX': sizeX,
            'sizeY': sizeY,
            'initial_position': [init_posX, init_posY],
            'dirt_rate': dirt_rate
        }), 201
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/environment/<env_id>', methods=['DELETE'])
def delete_environment(env_id):
    if env_server.delete_environment(env_id):
        return jsonify({'message': 'Environment deleted successfully'}), 200
    else:
        return jsonify({'error': 'Environment not found'}), 404

@app.route('/api/environment/<env_id>/state', methods=['GET'])
def get_environment_state(env_id):
    env = env_server.get_environment(env_id)
    if not env:
        return jsonify({'error': 'Environment not found'}), 404
    
    agent_x, agent_y = env.get_agent_position()
    
    return jsonify({
        'environment_id': env_id,
        'agent_position': [agent_x, agent_y],
        'is_dirty': bool(env.is_dirty()),
        'performance': env.get_performance(),
        'actions_taken': env.actions_taken,
        'actions_remaining': env.get_actions_remaining(),
        'is_finished': bool(env.is_finished()),
        'completion_reason': getattr(env, 'completion_reason', None),
        'grid': env.get_grid_copy().tolist()
    })

@app.route('/api/environment/<env_id>/action', methods=['POST'])
def execute_action(env_id):
    env = env_server.get_environment(env_id)
    if not env:
        return jsonify({'error': 'Environment not found'}), 404
    
    try:
        data = request.get_json()
        action_str = data.get('action')
        
        if not action_str:
            return jsonify({'error': 'Action required'}), 400
        
        action_map = {
            'up': Action.UP,
            'down': Action.DOWN,
            'left': Action.LEFT,
            'right': Action.RIGHT,
            'suck': Action.SUCK,
            'idle': Action.IDLE
        }
        
        if action_str.lower() not in action_map:
            return jsonify({'error': 'Invalid action'}), 400
        
        action = action_map[action_str.lower()]
        
        prev_performance = env.get_performance()
        prev_position = env.get_agent_position()
        prev_dirty = env.is_dirty()
        
        success = env.accept_action(action)
        
        new_performance = env.get_performance()
        new_position = env.get_agent_position()
        new_dirty = env.is_dirty()
        
        return jsonify({
            'success': success,
            'action': action_str,
            'previous_state': {
                'position': list(prev_position),
                'is_dirty': bool(prev_dirty),
                'performance': prev_performance
            },
            'new_state': {
                'position': list(new_position),
                'is_dirty': bool(new_dirty),
                'performance': new_performance,
                'actions_taken': env.actions_taken,
                'actions_remaining': env.get_actions_remaining(),
                'is_finished': bool(env.is_finished()),
                'completion_reason': getattr(env, 'completion_reason', None)
            },
            'reward': new_performance - prev_performance
        })
    
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@app.route('/api/environment/<env_id>/sense', methods=['GET'])
def sense_environment(env_id):
    env = env_server.get_environment(env_id)
    if not env:
        return jsonify({'error': 'Environment not found'}), 404
    
    agent_x, agent_y = env.get_agent_position()
    
    return jsonify({
        'position': [agent_x, agent_y],
        'is_dirty': bool(env.is_dirty()),
        'actions_remaining': env.get_actions_remaining(),
        'is_finished': bool(env.is_finished()),
        'completion_reason': getattr(env, 'completion_reason', None)
    })

@app.route('/api/environments', methods=['GET'])
def list_environments():
    with env_server.lock:
        env_list = []
        for env_id, env_data in env_server.environments.items():
            env = env_data['environment']
            agent_x, agent_y = env.get_agent_position()
            env_list.append({
                'environment_id': env_id,
                'created_at': env_data['created_at'],
                'last_access': env_data['last_access'],
                'size': [env.sizeX, env.sizeY],
                'agent_position': [agent_x, agent_y],
                'performance': env.get_performance(),
                'actions_taken': env.actions_taken,
                'is_finished': bool(env.is_finished())
            })
    
    return jsonify({'environments': env_list})

@app.route('/api/cleanup', methods=['POST'])
def cleanup_environments():
    data = request.get_json() or {}
    max_age = data.get('max_age', 3600)
    deleted_count = env_server.cleanup_old_environments(max_age)
    return jsonify({'deleted_environments': deleted_count})

@app.route('/api/health', methods=['GET'])
def health_check():
    return jsonify({
        'status': 'healthy',
        'active_environments': len(env_server.environments),
        'timestamp': time.time()
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Endpoint not found'}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({'error': 'Internal server error'}), 500

def cleanup_thread():
    while True:
        time.sleep(300)
        env_server.cleanup_old_environments()

if __name__ == '__main__':
    cleanup_thread = threading.Thread(target=cleanup_thread, daemon=True)
    cleanup_thread.start()
    
    print("Starting Vacuum Environment Server...")
    print("API Documentation:")
    print("POST /api/environment - Create new environment")
    print("GET  /api/environment/<id>/state - Get environment state")
    print("POST /api/environment/<id>/action - Execute action")
    print("GET  /api/environment/<id>/sense - Get agent perception")
    print("GET  /api/environments - List all environments")
    print("POST /api/cleanup - Cleanup old environments")
    print("GET  /api/health - Health check")
    
    app.run(host='0.0.0.0', port=5000, debug=True, threaded=True)