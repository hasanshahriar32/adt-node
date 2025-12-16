# Agriculture Digital Twin Project - Progress Documentation

## Project Overview
An IoT-based smart agriculture system that integrates real-time sensor data with AI predictions and Digital Twin technology for intelligent crop recommendations.

## Architecture
```
Weather API → Node-RED → Azure IoT Hub → Azure Digital Twins → Visualization
                ↓
         AI Model (Flexible Location)
              ↓
    Edge (Raspberry Pi) OR Cloud (Azure Functions)
```

## Current Status: Phase 3 Complete ✅

### Phase 1: Weather Integration ✅
- **Completed**: WeatherAPI.com integration
- **Location**: Dhaka, Bangladesh
- **Features**:
  - Real-time temperature, humidity, rainfall data
  - Fallback mechanism for API failures
  - 5-minute data refresh cycle

### Phase 2: Data Processing & Simulation ✅
- **Completed**: Physics-based soil moisture simulation
- **Features**:
  - Rainfall increases soil moisture (+2x factor)
  - Temperature decreases moisture (evaporation: -0.05x factor)
  - Clamped values: 10% - 60%
  - Persistent state management

### Phase 3: Azure IoT Hub Connection ✅
- **Completed**: Secure MQTT connection to Azure IoT Hub
- **Configuration**:
  - IoT Hub: `researchdt.azure-devices.net`
  - Device ID: `pc_sim_01`
  - Protocol: MQTT over TLS (port 8883)
  - Authentication: SAS Token (dynamically generated)
  
- **Data Schema**:
```json
{
  "schemaVersion": "1.0",
  "eventType": "telemetry",
  "messageId": 123,
  "deviceId": "pc_sim_01",
  "farmId": "farm_001",
  "zoneId": "zone_A",
  "telemetry": {
    "temperature": 30.5,
    "humidity": 70,
    "soilMoisture": 45.2
  },
  "actuators": {
    "pump": "OFF"
  },
  "system": {
    "deviceType": "simulator",
    "firmware": "v0.1",
    "status": "online",
    "dataSource": "WeatherAPI.com"
  },
  "timestamp": "2025-12-14T21:39:15.000Z"
}
```

- **Heartbeat**: Every 60 seconds
- **Dashboard**: Available at `/ui` with real-time monitoring

## Deployment

### Local Development
```bash
cd simulation
./start_simulation.sh
# Access at http://localhost:1880
# Dashboard at http://localhost:1880/ui
```

### Docker Deployment (Render.com)
- **URL**: https://adt-node.onrender.com
- **Port**: 10000
- **Environment Variables**:
  - `WEATHER_API_KEY`: WeatherAPI key
  - `IOT_HUB_HOSTNAME`: researchdt.azure-devices.net
  - `DEVICE_ID`: pc_sim_01
  - `IOT_HUB_SAS_KEY`: Azure device primary key
  - `WEATHER_LOCATION`: Dhaka

### Security
- All secrets in `.gitignore`
- Runtime files generated dynamically
- SAS tokens auto-generated with 1-year expiry

## Technology Stack
- **Node-RED**: v4.1.2
- **Node.js**: v20.19.6
- **Python**: 3.x (for SAS token generation)
- **Dashboard**: Node-RED Dashboard v3.6.6
- **Protocol**: MQTT/TLS
- **Cloud**: Azure IoT Hub

## File Structure
```
simulation/
├── .env                          # Secrets (gitignored)
├── .gitignore
├── Dockerfile                    # Docker configuration
├── flows.json                    # Node-RED flow template
├── flows_runtime.json            # Generated at runtime
├── flows_runtime_cred.json       # Generated credentials
├── generate_sas.py               # SAS token generator
├── start_simulation.sh           # Startup script
├── settings.js                   # Node-RED settings
├── package.json                  # Dependencies
└── README.md                     # Usage guide
```

## Next Phases

### Phase 4: AI Model Integration (Flexible Architecture)
**Objective**: Enable crop prediction using Random Forest model with flexible deployment

**Options**:
1. **Edge Computing** (Raspberry Pi):
   - Run model locally on device
   - Low latency predictions
   - Reduced cloud costs
   - Works offline

2. **Cloud Computing** (Azure Functions):
   - Centralized model management
   - Easier updates/retraining
   - Scalable across multiple devices
   - Advanced analytics

**Implementation Strategy**:
- Create unified data format for both paths
- Add routing logic in Node-RED
- Model inference endpoint (Python script for Pi, Azure Function for cloud)
- Enhanced payload with AI predictions

### Phase 5: Azure Digital Twins Setup
**Objective**: Create digital representation of farm infrastructure

**Components**:
1. **Digital Twin Definition Language (DTDL) Models**:
   - Farm
   - Zone
   - Device (Sensor)
   - Crop

2. **Relationships**:
   - Farm → contains → Zones
   - Zone → contains → Devices
   - Zone → grows → Crop

3. **Azure Function**: Process IoT Hub data → Update Digital Twin

### Phase 6: Visualization & Analytics
**Objective**: Real-time monitoring and historical analysis

**Features**:
- Digital Twin Explorer integration
- Time-series data visualization
- Crop recommendation dashboard
- Alert system for anomalies

## Research Metrics (From Manuscript)
- **Model Accuracy**: 96% (Random Forest)
- **Precision**: 0.95
- **Recall**: 0.94
- **F1-Score**: 0.94
- **Training Dataset**: Multi-source agricultural data

## References
- Azure IoT Hub: https://docs.microsoft.com/azure/iot-hub/
- Node-RED: https://nodered.org/docs/
- WeatherAPI: https://www.weatherapi.com/docs/
- Azure Digital Twins: https://docs.microsoft.com/azure/digital-twins/
