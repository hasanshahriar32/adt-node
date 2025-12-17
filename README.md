# Azure Digital Twins & IoT Project

This project implements a complete IoT solution using Azure Digital Twins, Azure IoT Hub, and Node-RED for simulation.

## ✅ Current Status: FULLY OPERATIONAL

**Live Data Pipeline**: Node-RED → IoT Hub → Event Grid → Azure Function → Digital Twin  
**Last Verified**: December 17, 2025  
**Update Frequency**: ~60 seconds

📊 **View Live Data**: [Azure Digital Twins Explorer](https://explorer.digitaltwins.azure.net)  
📖 **Full Status**: See [SYSTEM_STATUS.md](./SYSTEM_STATUS.md)

## 🚀 Project Progress

| Phase | Description | Status | Location |
|-------|-------------|--------|----------|
| **Phase 1** | **PC-Based Simulation** - Node-RED flow generating realistic telemetry. | ✅ **Completed** | `simulation/` |
| **Phase 2** | **Data Contract Definition** - JSON schema for telemetry and heartbeat. | ✅ **Completed** | `simulation/flows.json` |
| **Phase 3** | **Azure IoT Hub Connectivity** - MQTT connection to cloud. | ✅ **Completed** | `simulation/` |
| **Phase 3.5** | **Weather-Driven Simulation** - Real external data (OpenWeatherMap API) fused with physics-based soil model. | ✅ **Completed** | `simulation/` |
| **Phase 4** | **Digital Twins Modeling** - DTDL models for Zone, Device with Properties. | ✅ **Completed** | `digital-twins/` |
| **Phase 5** | **Azure Functions** - Event Grid triggered function updating Twins. | ✅ **Completed** | `azure-functions/` |
| **Phase 6** | **Event Grid Integration** - IoT Hub → Event Grid → Function → Twin. | ✅ **Completed** | Azure Portal |

## 📂 Project Structure

The project is organized into the following modules:

### 1. `simulation/`

Contains the **Node-RED** based simulator that runs locally on your PC.

- **Features**:
  - Fetches real weather data from **OpenWeatherMap API** (Temperature, Humidity, Rainfall, Wind).
  - **Physics-based soil simulation**: Soil moisture responds to rainfall (increases) and temperature/evaporation (decreases).
  - Sends **Telemetry** events (every 5 minutes).
  - Sends **Heartbeat** events (every 60s).
  - Connects to **Azure IoT Hub** via MQTT.
- **Key Files**: `flows.json`, `start_simulation.sh`.
- **Data Source**: Hybrid digital twin (real weather + simulated soil physics).

### 2. `docs/`

Project documentation and guides.

- `phase1_simulation_guide.md`: The detailed guide for the simulation logic and setup.

### 3. `digital-twins/`

Will contain the **DTDL (Digital Twins Definition Language)** models.

- **Purpose**: Defines the graph structure (Farm ➡ Zone ➡ Sensor).

### 4. `azure-functions/`

Contains the **Azure Functions** code (Python 3.11) deployed to Azure.

- **Function**: `IoTHub_EventGrid` - Event Grid triggered function
- **Purpose**: Receives telemetry from IoT Hub via Event Grid and updates Digital Twin properties
- **Status**: ✅ Deployed and running (adt-telemetry-router)
- **Trigger**: Event Grid (Microsoft.Devices.DeviceTelemetry events)

## 🛠️ Getting Started

To run the simulation:

1. **Navigate to the simulation folder**:

   ```bash
   cd simulation
   ```

2. **Start the simulator**:

   ```bash
   ./start_simulation.sh
   ```

3. **Open Node-RED**:
   - Go to [http://localhost:1880](http://localhost:1880).
   - Configure the **Azure IoT Hub** node with your specific connection details (see `simulation/README.md`).
