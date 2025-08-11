import requests
import json
import time
from typing import Dict, List, Optional, Tuple

class VacuumEnvironmentClient:
    def __init__(self, server_url: str = "http://localhost:5000"):
        self.server_url = server_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
    
    def create_environment(self, sizeX: int = 8, sizeY: int = 8, 
                          init_posX: Optional[int] = None, 
                          init_posY: Optional[int] = None, 
                          dirt_rate: float = 0.3, seed: Optional[int] = None) -> Optional[str]:
        if init_posX is None:
            init_posX = sizeX // 2
        if init_posY is None:
            init_posY = sizeY // 2
            
        data = {
            'sizeX': sizeX,
            'sizeY': sizeY,
            'init_posX': init_posX,
            'init_posY': init_posY,
            'dirt_rate': dirt_rate
        }
        
        if seed is not None:
            data['seed'] = seed
        
        try:
            response = self.session.post(f"{self.server_url}/api/environment", 
                                       json=data)
            if response.status_code == 201:
                return response.json()['environment_id']
            else:
                print(f"Error creating environment: {response.json().get('error', 'Unknown error')}")
                return None
        except requests.RequestException as e:
            print(f"Connection error: {e}")
            return None
    
    def delete_environment(self, env_id: str) -> bool:
        try:
            response = self.session.delete(f"{self.server_url}/api/environment/{env_id}")
            return response.status_code == 200
        except requests.RequestException:
            return False
    
    def get_state(self, env_id: str) -> Optional[Dict]:
        try:
            response = self.session.get(f"{self.server_url}/api/environment/{env_id}/state")
            if response.status_code == 200:
                return response.json()
            return None
        except requests.RequestException:
            return None
    
    def execute_action(self, env_id: str, action: str) -> Optional[Dict]:
        data = {'action': action}
        try:
            response = self.session.post(f"{self.server_url}/api/environment/{env_id}/action",
                                       json=data)
            if response.status_code == 200:
                return response.json()
            else:
                print(f"Action error: {response.json().get('error', 'Unknown error')}")
                return None
        except requests.RequestException as e:
            print(f"Connection error: {e}")
            return None
    
    def sense(self, env_id: str) -> Optional[Dict]:
        try:
            response = self.session.get(f"{self.server_url}/api/environment/{env_id}/sense")
            if response.status_code == 200:
                return response.json()
            return None
        except requests.RequestException:
            return None
    
    def list_environments(self) -> Optional[List[Dict]]:
        try:
            response = self.session.get(f"{self.server_url}/api/environments")
            if response.status_code == 200:
                return response.json()['environments']
            return None
        except requests.RequestException:
            return None
    
    def health_check(self) -> bool:
        try:
            response = self.session.get(f"{self.server_url}/api/health")
            return response.status_code == 200
        except requests.RequestException:
            return False
    
    def wait_for_server(self, timeout: int = 30) -> bool:
        start_time = time.time()
        while time.time() - start_time < timeout:
            if self.health_check():
                return True
            time.sleep(1)
        return False

class EnvironmentProxy:
    def __init__(self, client: VacuumEnvironmentClient, env_id: str):
        self.client = client
        self.env_id = env_id
        self._cached_state = None
        self._last_update = 0
    
    def _update_cache(self, force: bool = False):
        current_time = time.time()
        if force or current_time - self._last_update > 0.1:
            self._cached_state = self.client.get_state(self.env_id)
            self._last_update = current_time
    
    def get_agent_position(self) -> Tuple[int, int]:
        self._update_cache()
        if self._cached_state:
            pos = self._cached_state['agent_position']
            return pos[0], pos[1]
        return 0, 0
    
    def is_dirty(self) -> bool:
        self._update_cache()
        return self._cached_state['is_dirty'] if self._cached_state else False
    
    def get_performance(self) -> int:
        self._update_cache()
        return self._cached_state['performance'] if self._cached_state else 0
    
    def get_actions_remaining(self) -> int:
        self._update_cache()
        return self._cached_state['actions_remaining'] if self._cached_state else 0
    
    def is_finished(self) -> bool:
        self._update_cache()
        return self._cached_state['is_finished'] if self._cached_state else True
    
    def get_grid_copy(self):
        self._update_cache()
        if self._cached_state and 'grid' in self._cached_state:
            import numpy as np
            return np.array(self._cached_state['grid'])
        return None
    
    @property
    def actions_taken(self) -> int:
        self._update_cache()
        return self._cached_state['actions_taken'] if self._cached_state else 0
    
    @property
    def max_actions(self) -> int:
        return 1000
    
    @property
    def sizeX(self) -> int:
        self._update_cache()
        if self._cached_state and 'grid' in self._cached_state:
            return len(self._cached_state['grid'][0]) if self._cached_state['grid'] else 0
        return 0
    
    @property
    def sizeY(self) -> int:
        self._update_cache()
        if self._cached_state and 'grid' in self._cached_state:
            return len(self._cached_state['grid']) if self._cached_state['grid'] else 0
        return 0
    
    def accept_action(self, action) -> bool:
        action_str = action.value if hasattr(action, 'value') else str(action)
        result = self.client.execute_action(self.env_id, action_str)
        if result:
            self._update_cache(force=True)
            return result['success']
        return False