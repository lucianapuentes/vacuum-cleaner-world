# Vacuum Environment Server API Documentation

## Overview

La API REST del servidor de entornos de aspiradora permite crear y gestionar múltiples simulaciones de forma concurrente. El servidor actúa como el "mundo" donde los agentes pueden conectarse y ejecutar acciones.

### Integración con BaseAgent

Todos los agentes ahora heredan de **BaseAgent**, que proporciona:
- **UI integrada**: Visualización pygame opcional
- **Sistema de grabación**: Grabación completa a JSON
- **Sistema de replay**: Reproducción de simulaciones
- **Configuración unificada**: Parámetros consistentes
- **Extensibilidad**: Los agentes solo implementan `think()`

Ver [README.md](README.md) para detalles completos de la nueva arquitectura.

## Base URL
```
http://localhost:5000/api
```

## Endpoints

### 1. Crear Entorno
**POST** `/environment`

Crea un nuevo entorno de simulación.

**Request Body:**
```json
{
  "sizeX": 8,
  "sizeY": 8,
  "init_posX": 4,
  "init_posY": 4,
  "dirt_rate": 0.3
}
```

**Response (201):**
```json
{
  "environment_id": "uuid-string",
  "sizeX": 8,
  "sizeY": 8,
  "initial_position": [4, 4],
  "dirt_rate": 0.3
}
```

### 2. Estado del Entorno
**GET** `/environment/{env_id}/state`

Obtiene el estado completo del entorno.

**Response (200):**
```json
{
  "environment_id": "uuid-string",
  "agent_position": [3, 4],
  "is_dirty": true,
  "performance": 15,
  "actions_taken": 145,
  "actions_remaining": 855,
  "is_finished": false,
  "grid": [[0, 1, 0], [1, 0, 1], [0, 0, 0]]
}
```

### 3. Ejecutar Acción
**POST** `/environment/{env_id}/action`

Ejecuta una acción del agente en el entorno.

**Request Body:**
```json
{
  "action": "up"
}
```

**Acciones válidas:** `up`, `down`, `left`, `right`, `suck`, `idle`

**Response (200):**
```json
{
  "success": true,
  "action": "up",
  "previous_state": {
    "position": [3, 4],
    "is_dirty": true,
    "performance": 15
  },
  "new_state": {
    "position": [3, 3],
    "is_dirty": false,
    "performance": 15,
    "actions_taken": 146,
    "actions_remaining": 854,
    "is_finished": false
  },
  "reward": 0
}
```

### 4. Percepción del Agente
**GET** `/environment/{env_id}/sense`

Obtiene la percepción actual del agente (información limitada).

**Response (200):**
```json
{
  "position": [3, 3],
  "is_dirty": false,
  "actions_remaining": 854,
  "is_finished": false
}
```

### 5. Listar Entornos
**GET** `/environments`

Lista todos los entornos activos en el servidor.

**Response (200):**
```json
{
  "environments": [
    {
      "environment_id": "uuid-string",
      "created_at": 1640995200.123,
      "last_access": 1640995300.456,
      "size": [8, 8],
      "agent_position": [3, 3],
      "performance": 15,
      "actions_taken": 146,
      "is_finished": false
    }
  ]
}
```

### 6. Eliminar Entorno
**DELETE** `/environment/{env_id}`

Elimina un entorno específico.

**Response (200):**
```json
{
  "message": "Environment deleted successfully"
}
```

### 7. Limpiar Entornos Antiguos
**POST** `/cleanup`

Elimina entornos no utilizados recientemente.

**Request Body (opcional):**
```json
{
  "max_age": 3600
}
```

**Response (200):**
```json
{
  "deleted_environments": 3
}
```

### 8. Health Check
**GET** `/health`

Verifica el estado del servidor.

**Response (200):**
```json
{
  "status": "healthy",
  "active_environments": 5,
  "timestamp": 1640995400.789
}
```

## Códigos de Error

- **400 Bad Request**: Parámetros inválidos
- **404 Not Found**: Entorno no encontrado
- **500 Internal Server Error**: Error del servidor

**Ejemplo de respuesta de error:**
```json
{
  "error": "Environment not found"
}
```

## Límites y Restricciones

- **Tamaño del entorno**: 1x1 a 256x256
- **Rate de suciedad**: 0.0 a 1.0
- **Acciones máximas**: 1000 per simulación
- **Timeout automático**: Entornos sin acceso por 1 hora se eliminan automáticamente

## Ejemplos de Uso

### Python con requests
```python
import requests

# Crear entorno
response = requests.post('http://localhost:5000/api/environment', json={
    'sizeX': 8, 'sizeY': 8, 'dirt_rate': 0.3
})
env_id = response.json()['environment_id']

# Ejecutar acción
requests.post(f'http://localhost:5000/api/environment/{env_id}/action', 
              json={'action': 'suck'})

# Obtener estado
state = requests.get(f'http://localhost:5000/api/environment/{env_id}/state')
print(state.json())
```

### cURL
```bash
# Crear entorno
curl -X POST http://localhost:5000/api/environment \
  -H "Content-Type: application/json" \
  -d '{"sizeX":8,"sizeY":8,"dirt_rate":0.3}'

# Ejecutar acción
curl -X POST http://localhost:5000/api/environment/{env_id}/action \
  -H "Content-Type: application/json" \
  -d '{"action":"up"}'
```

## Arquitectura Cliente-Servidor

### Servidor (environment_server.py)
- Gestiona múltiples entornos concurrentemente
- API REST con Flask
- Limpieza automática de entornos antiguos
- Thread-safe operations

### Cliente (api_client.py)
- Wrapper Python para la API
- Manejo de errores y reconexión
- Cache de estado para eficiencia

### BaseAgent (base_agent.py)
- Clase base abstracta para todos los agentes
- UI integrada con pygame (opcional)
- Sistema de grabación y replay
- Configuración paramétrica flexible
- Los agentes específicos solo implementan think()

### Agentes Específicos
- Heredan de BaseAgent
- Solo implementan el método think()
- Comunicación HTTP transparente
- UI, grabación y replay automáticos

## Flujo de Trabajo Típico

### Con BaseAgent (Recomendado)
1. **Iniciar servidor**: `python environment_server.py`
2. **Usar run_agent.py**: `python run_agent.py --agent-file agents/example_agent.py --ui --record`
3. **BaseAgent maneja**: Conexión, simulación, UI, grabación automáticamente
4. **Finalización**: Desconexión y limpieza automática

### Manual (API Directa)
1. **Iniciar servidor**: `python environment_server.py`
2. **Cliente se conecta**: Crea entorno via POST
3. **Simulación**: Bucle de sense-think-act
4. **Finalización**: Entorno se elimina automáticamente

## Seguridad y Rendimiento

- **CORS habilitado** para desarrollo web
- **Threading** para múltiples clientes
- **Rate limiting** via límite de acciones
- **Memory cleanup** automático
- **Error handling** robusto
