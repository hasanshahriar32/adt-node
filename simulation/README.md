# PC-Based Simulation

This folder contains the local Node-RED simulation environment for Phase 1.

## Setup

1. Dependencies are already installed in this folder (`node_modules`).
2. The flow definition is in `flows.json`.

## Running the Simulation

Run the start script:

```bash
./start_simulation.sh
```

Then open your browser at [http://localhost:1880](http://localhost:1880).

## What's Included

- **Weather API Integration**: Fetches real weather data from WeatherAPI.com every 5 minutes.
- **Weather Parser**: Extracts temperature, humidity, rainfall, wind speed, and cloud cover.
- **Physics-Based Soil Fusion**: Calculates soil moisture using:
  - Rainfall increases moisture.
  - Temperature/evaporation decreases moisture.
- **Format Payload**: Formats data into the required Azure IoT JSON structure with `messageId`, `eventType`, `schemaVersion`, and `dataSource`.
- **Heartbeat**: Sends device health heartbeat every 60 seconds.
- **Azure IoT Hub Output**: MQTT output node configured to send data to Azure IoT Hub.
- **Debug Output**: View weather data, fused results, and final payloads in the debug sidebar.

## Configuration

The simulation is configured using a `.env` file.

1.  **Edit the `.env` file**:
    Open `simulation/.env` and update the following values:

    ```ini
    # Weather Configuration
    WEATHER_API_KEY=your_actual_api_key
    WEATHER_LOCATION=Dhaka

    # Azure IoT Hub Configuration
    IOT_HUB_HOSTNAME=your-hub-name.azure-devices.net
    DEVICE_ID=pc_sim_01
    IOT_HUB_SAS_KEY=your_sas_token_or_primary_key
    ```

2.  **Restart the Simulation**:
    If the simulation is running, stop it (Ctrl+C) and start it again for changes to take effect.

    ```bash
    ./start_simulation.sh
    ```

## Weather API Configuration

1. **Get an API key from WeatherAPI.com**:
   - Sign up at [https://www.weatherapi.com/](https://www.weatherapi.com/).
   - Copy your API key into the `.env` file.

## Azure IoT Hub Configuration

1. **Get your Connection Details**:
   - Go to Azure Portal -> IoT Hub -> Devices.
   - Copy your **Device ID** and **SAS Token** (or Primary Key).
   - Update the `.env` file.
