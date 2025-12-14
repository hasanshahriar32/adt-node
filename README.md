# Azure Digital Twins & IoT Project

This project implements a complete IoT solution using Azure Digital Twins, Azure IoT Hub, and Node-RED for simulation.

## 🚀 Project Progress

| Phase | Description | Status | Location |
|-------|-------------|--------|----------|
| **Phase 1** | **PC-Based Simulation** - Node-RED flow generating realistic telemetry. | ✅ **Completed** | `simulation/` |
| **Phase 2** | **Data Contract Definition** - JSON schema for telemetry and heartbeat. | ✅ **Completed** | `simulation/flows.json` |
| **Phase 3** | **Azure IoT Hub Connectivity** - MQTT connection to cloud. | ✅ **Completed** | `simulation/` |
| **Phase 3.5** | **Weather-Driven Simulation** - Real external data (OpenWeatherMap API) fused with physics-based soil model. | ✅ **Completed** | `simulation/` |
| **Phase 4** | **Digital Twins Modeling** - DTDL models for Farm, Zone, Sensor. | ⏳ *Pending* | `digital-twins/` |
| **Phase 5** | **Azure Functions** - Serverless compute to update Twins. | ⏳ *Pending* | `azure-functions/` |

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

Will contain the **Azure Functions** code (likely Python or JavaScript).

- **Purpose**: Ingests data from IoT Hub and updates the Digital Twins graph.

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
