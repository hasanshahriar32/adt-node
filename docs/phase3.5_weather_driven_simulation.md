# Phase 3.5: Weather-Driven Simulation Guide

This document explains how the **weather-driven simulation** works and why it's a valid approach for digital twin projects without physical hardware.

## Concept

Instead of generating random sensor values, we now:

1. **Fetch real weather data** from WeatherAPI.com (Temperature, Humidity, Rainfall, Wind).
2. **Simulate soil moisture** using physics-based rules:
   - Rainfall increases soil moisture.
   - Temperature (evaporation) decreases soil moisture.
3. **Send hybrid telemetry** to Azure IoT Hub.

This creates a **software digital twin** that responds to real-world conditions.

## Why This Approach?

### Industry Standard
- Many digital twin projects start with **API-driven simulation** before deploying physical sensors.
- This is common in agriculture, energy, and manufacturing.

### Academically Defensible
- You're not making up data; you're using **real external signals**.
- The soil model uses **physics-inspired rules** (not just randomness).

### Hardware-Independent
- No Raspberry Pi or sensors needed yet.
- You can still demonstrate the full IoT → Cloud → Digital Twin pipeline.

## Data Flow

```
WeatherAPI.com
   ↓
Weather Parser (Extract: temp, humidity, rainfall)
   ↓
Soil Fusion (Physics-based calculation)
   ↓
Format Payload (Azure IoT JSON schema)
   ↓
MQTT → Azure IoT Hub
```

## Physics-Based Soil Model

The soil moisture calculation uses simple physics:

```javascript
soil += rainfall * 2;           // Rain increases moisture
soil -= temperature * 0.05;     // Heat/evaporation decreases moisture
soil = clamp(soil, 10, 60);     // Keep in realistic range
```

This is **not ML**, but it's a valid **rule-based model** used in early-stage digital twins.

## Example Telemetry Output

```json
{
  "schemaVersion": "1.0",
  "eventType": "telemetry",
  "messageId": 42,
  "deviceId": "pc_sim_01",
  "farmId": "farm_001",
  "zoneId": "zone_A",
  "telemetry": {
    "temperature": 31.2,
    "humidity": 78,
    "soilMoisture": 34.1
  },
  "system": {
    "deviceType": "simulator",
    "firmware": "v0.1",
    "status": "online",
    "dataSource": "OpenWeatherMap"
  },
  "timestamp": "2025-12-13T12:10:00Z"
}
```

Notice the `dataSource` field—this makes it clear that the data is API-driven, not from physical sensors.

## What's Next?

Once this is running and sending data to Azure IoT Hub:

### Phase 4: Azure Digital Twins
- Define DTDL models (Farm, Zone, Sensor).
- Create twin instances.
- Use Azure Functions to update twin properties from telemetry.

### Phase 5: Visualization & Insights
- Query the Digital Twins graph.
- Build dashboards.
- Add ML for predictive analytics.

## Validating Your Setup

Before moving to Phase 4, confirm:

- [ ] Weather API returns valid data (check debug output).
- [ ] Soil moisture changes realistically based on weather.
- [ ] Telemetry arrives in Azure IoT Hub.
- [ ] `dataSource` field is set to `"OpenWeatherMap"`.

If all checks pass, you're ready for Digital Twins.
