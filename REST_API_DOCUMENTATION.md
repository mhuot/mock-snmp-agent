# Mock SNMP Agent REST API Documentation

## Overview

The Mock SNMP Agent provides a comprehensive REST API for controlling and monitoring the agent, managing test scenarios, and accessing real-time data through WebSocket connections. This API enables programmatic control for automated testing, CI/CD integration, and monitoring applications.

## Quick Start

```bash
# Start agent with API enabled
python mock_snmp_agent.py --rest-api --api-port 8080 --port 11611

# Test basic connectivity
curl http://localhost:8080/health

# Get current metrics
curl http://localhost:8080/metrics
```

## Base URL

```
http://localhost:8080
```

## Authentication

Currently, the API does not require authentication. In production deployments, consider adding authentication middleware such as API keys or JWT tokens.

## Error Handling

All API responses follow a consistent error format:

```json
{
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Invalid parameter value",
    "details": {
      "field": "delay",
      "value": "invalid",
      "expected": "number"
    }
  }
}
```

Common HTTP status codes:
- `200`: Success
- `400`: Bad Request (invalid parameters)
- `404`: Not Found (resource doesn't exist)
- `422`: Unprocessable Entity (validation failed)
- `500`: Internal Server Error

## Core Endpoints

### Health Check

```http
GET /health
```

Returns the current health status of the agent.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": 1640995200.0,
  "uptime_seconds": 3600.0,
  "version": "1.0.0",
  "snmp_endpoint": "127.0.0.1:11611",
  "api_version": "v1",
  "features": {
    "websockets": true,
    "simulation_behaviors": ["delay", "drops", "counter_wrap"],
    "supported_snmp_versions": ["v1", "v2c", "v3"]
  }
}
```

**Status Codes:**
- `200`: Agent is healthy and operational
- `503`: Agent is starting up or experiencing issues

**Example Usage:**
```python
import requests

response = requests.get('http://localhost:8080/health')
if response.status_code == 200:
    data = response.json()
    print(f"Agent uptime: {data['uptime_seconds']} seconds")
else:
    print("Agent not healthy")
```

### Metrics

```http
GET /metrics
```

Returns performance metrics for the agent.

**Response:**
```json
{
  "timestamp": 1640995200.0,
  "uptime_seconds": 3600.0,
  "requests_total": 1000,
  "requests_successful": 950,
  "requests_failed": 50,
  "avg_response_time_ms": 75.5,
  "current_connections": 5
}
```

### Configuration

#### Get Configuration

```http
GET /config
```

Returns the current agent configuration.

#### Update Configuration

```http
PUT /config
Content-Type: application/json
```

**Request Body:**
```json
{
  "simulation": {
    "behaviors": {
      "delay": {
        "enabled": true,
        "global_delay": 100,
        "deviation": 50
      }
    }
  }
}
```

### Agent Control

#### Get Agent Status

```http
GET /agent/status
```

Returns detailed agent status information.

#### Restart Agent

```http
POST /agent/restart
Content-Type: application/json
```

**Request Body:**
```json
{
  "force": false,
  "timeout_seconds": 30
}
```

## Enhanced Query Endpoints

### Query OIDs

```http
POST /oids/query
Content-Type: application/json
```

Query specific OID values with metadata.

**Request Body:**
```json
{
  "oids": ["1.3.6.1.2.1.1.1.0", "1.3.6.1.2.1.1.3.0"],
  "community": "public",
  "include_metadata": true
}
```

### Search OIDs

```http
GET /oids/search?pattern=1.3.6.1.2.1&mib=SNMPv2-MIB&limit=50
```

Search for OIDs by pattern or MIB.

### Get OID Tree

```http
GET /oids/tree?root_oid=1.3.6.1&max_depth=3
```

Get hierarchical OID tree structure for visualization.

### Metrics History

```http
POST /metrics/history
Content-Type: application/json
```

Get historical metrics data.

**Request Body:**
```json
{
  "start_time": 1640991600.0,
  "end_time": 1640995200.0,
  "interval_minutes": 5,
  "metrics": ["requests_total", "avg_response_time_ms"]
}
```

### State History

```http
GET /state/history?device_type=router
```

Get state machine transition history.

## Simulation Control

### List Scenarios

```http
GET /simulation/scenarios
```

List all available test scenarios.

### Create Scenario

```http
POST /simulation/scenarios
Content-Type: application/json
```

**Request Body:**
```json
{
  "name": "High Load Test",
  "description": "Test agent under high load with delays",
  "duration_seconds": 300,
  "behaviors": [
    {
      "name": "delay",
      "enabled": true,
      "parameters": {
        "global_delay": 200
      }
    }
  ],
  "success_criteria": {
    "max_response_time_ms": 500,
    "min_success_rate": 95
  }
}
```

### Execute Scenario

```http
POST /simulation/execute
Content-Type: application/json
```

**Request Body:**
```json
{
  "scenario_id": "High Load Test",
  "override_duration": null,
  "dry_run": false
}
```

### Get Execution Status

```http
GET /simulation/executions/{execution_id}
```

### Control Behaviors

```http
POST /behaviors/control
Content-Type: application/json
```

**Request Body:**
```json
{
  "behaviors": {
    "delay": true,
    "drop": false,
    "snmpv3_security": true
  }
}
```

## Export/Import

### Export Data

```http
POST /export/data
Content-Type: application/json
```

**Request Body:**
```json
{
  "format": "json",
  "include_metrics": true,
  "include_config": true,
  "include_scenarios": true,
  "include_history": true,
  "time_range_hours": 24
}
```

### Export Archive

```http
GET /export/archive?include_metrics=true&include_config=true&include_scenarios=true&include_history=true&time_range_hours=24
```

Downloads a ZIP archive with all requested data.

### Import Data

```http
POST /import/data
Content-Type: multipart/form-data
```

Upload a JSON or ZIP file to import configurations and scenarios.

## WebSocket Endpoints

WebSocket connections provide real-time streaming of agent data.

### Real-time Metrics

```
ws://localhost:8080/ws/metrics
```

Streams metrics updates every 5 seconds.

**Message Format:**
```json
{
  "type": "metrics_update",
  "timestamp": 1640995200.0,
  "data": {
    "requests_total": 1000,
    "requests_successful": 950,
    "avg_response_time_ms": 75.5
  }
}
```

### Real-time Logs

```
ws://localhost:8080/ws/logs
```

Streams log entries as they occur.

**Message Format:**
```json
{
  "type": "log_entry",
  "timestamp": 1640995200.0,
  "data": {
    "level": "info",
    "message": "SNMP request received",
    "source": "agent",
    "datetime": "2024-01-01T12:00:00"
  }
}
```

### State Machine Updates

```
ws://localhost:8080/ws/state
```

Streams state machine transitions.

**Message Format:**
```json
{
  "type": "state_transition",
  "timestamp": 1640995200.0,
  "data": {
    "device_type": "router",
    "old_state": "booting",
    "new_state": "operational",
    "trigger": "time_based",
    "reason": "Boot sequence completed"
  }
}
```

### SNMP Activity

```
ws://localhost:8080/ws/snmp-activity
```

Streams SNMP request/response activity.

**Message Format:**
```json
{
  "type": "snmp_activity",
  "timestamp": 1640995200.0,
  "data": {
    "request_type": "GET",
    "oid": "1.3.6.1.2.1.1.1.0",
    "community": "public",
    "source_ip": "192.168.1.100",
    "success": true,
    "response_time_ms": 45.2,
    "error_message": null
  }
}
```

### WebSocket Connection Stats

```http
GET /ws/stats
```

Returns statistics about active WebSocket connections.

## Error Responses

All endpoints return standardized error responses:

```json
{
  "error": "ValidationError",
  "message": "Invalid configuration format",
  "timestamp": 1640995200.0
}
```

Common HTTP status codes:
- `200 OK` - Successful operation
- `400 Bad Request` - Invalid request parameters
- `404 Not Found` - Resource not found
- `500 Internal Server Error` - Server error

## Example Usage

### Python Client Example

```python
import requests
import websocket
import json

# Base URL
BASE_URL = "http://localhost:8080"

# Get health status
response = requests.get(f"{BASE_URL}/health")
print(f"Health: {response.json()}")

# Update configuration
config_update = {
    "simulation": {
        "behaviors": {
            "delay": {
                "enabled": True,
                "global_delay": 100
            }
        }
    }
}
response = requests.put(f"{BASE_URL}/config", json=config_update)
print(f"Config updated: {response.json()}")

# Query specific OIDs
oid_query = {
    "oids": ["1.3.6.1.2.1.1.1.0", "1.3.6.1.2.1.1.3.0"],
    "include_metadata": True
}
response = requests.post(f"{BASE_URL}/oids/query", json=oid_query)
print(f"OID values: {response.json()}")

# Connect to WebSocket for real-time metrics
def on_message(ws, message):
    data = json.loads(message)
    print(f"Metric update: {data}")

ws = websocket.WebSocketApp("ws://localhost:8080/ws/metrics",
                          on_message=on_message)
ws.run_forever()
```

### JavaScript/React Example

```javascript
// Fetch current metrics
fetch('http://localhost:8080/metrics')
  .then(response => response.json())
  .then(data => console.log('Metrics:', data));

// Update configuration
const configUpdate = {
  simulation: {
    behaviors: {
      delay: {
        enabled: true,
        global_delay: 100
      }
    }
  }
};

fetch('http://localhost:8080/config', {
  method: 'PUT',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify(configUpdate)
})
  .then(response => response.json())
  .then(data => console.log('Config updated:', data));

// WebSocket connection for real-time updates
const ws = new WebSocket('ws://localhost:8080/ws/metrics');

ws.onmessage = (event) => {
  const data = JSON.parse(event.data);
  console.log('Metric update:', data);
};

ws.onerror = (error) => {
  console.error('WebSocket error:', error);
};
```

## API Documentation URLs

- **Interactive API Documentation**: http://localhost:8080/docs
- **ReDoc Documentation**: http://localhost:8080/redoc
- **OpenAPI Schema**: http://localhost:8080/openapi.json

## Rate Limiting

Currently, there are no rate limits implemented. In production, consider adding rate limiting middleware to prevent abuse.

## CORS Configuration

CORS is enabled by default for all origins. In production, configure specific allowed origins for security.

## Next Steps for React UI

With these REST API extensions, a React UI can now:

1. **Display real-time metrics** using WebSocket connections
2. **Browse and query OIDs** with the tree structure endpoint
3. **Create and execute test scenarios** with visual feedback
4. **View historical data** with charts and graphs
5. **Control agent behaviors** with toggle switches
6. **Export/import configurations** for sharing
7. **Monitor SNMP activity** in real-time
8. **Visualize state machine transitions** with diagrams

The API provides all necessary endpoints for a comprehensive monitoring and control interface.
