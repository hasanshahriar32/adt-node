# PC-Based Simulation First → Later Onboard to Raspberry Pi

This document shows **exactly how to continue without a Raspberry Pi**, by simulating the entire system on a PC/laptop first, and then migrating it to a Pi later with minimal changes.

This is a **correct and professional approach**. Many people do this.

---

## Why This Works (Important)

Node-RED is **hardware-agnostic**.

If your flows:
- use simulated sensors
- publish structured JSON
- send data to Azure

Then **the same flows will run on Raspberry Pi** later.

Only the *sensor input nodes* change.

---

## Phase 1A – Install Node-RED on PC (Simulation Environment)

### Objective
Run the full system locally on a PC.

### Steps (Windows / Linux / macOS)

1. Install **Node.js (LTS)**
2. Install Node-RED globally

```bash
npm install -g node-red
```

3. Start Node-RED

```bash
node-red
```

4. Open browser:
```
http://localhost:1880
```

5. Install Dashboard nodes:
- node-red-dashboard

---

## Phase 1B – Simulate Sensors (Instead of Real Hardware)

### Objective
Simulate **production-grade telemetry** that exactly matches what Azure IoT Hub and Azure Digital Twins expect later.

This phase is NOT random testing. It must produce **cloud-ready messages**.

---

### 1. Simulation Inputs (What You Generate)

You must simulate the **same signals real hardware would produce**.

#### Mandatory simulated inputs
- Temperature (°C)
- Humidity (%)
- Soil moisture (%)
- Device status (online/offline)
- Timestamp (UTC)

#### Optional but recommended
- Light intensity (lux)
- Battery / power level (%)
- Pump status (ON/OFF)

---

### 2. Sensor Simulation Rules (Important)

Do **not** generate fully random values.

Use **bounded, realistic ranges**:

| Sensor | Min | Max | Notes |
|------|-----|-----|------|
| Temperature | 18 | 40 | Bangladesh climate |
| Humidity | 50 | 95 | High humidity region |
| Soil Moisture | 10 | 60 | Field soil range |
| Light | 100 | 80,000 | Optional |

Add small variation per cycle, not jumps.

---

### 3. Core Node-RED Function (Simulation Engine)

This function replaces real sensors.

```javascript
let temp = flow.get('temp') || 28;
let hum = flow.get('hum') || 70;
let soil = flow.get('soil') || 30;

// smooth variation
temp += (Math.random() - 0.5);
hum += (Math.random() - 0.5) * 2;
soil += (Math.random() - 0.5) * 1.5;

// clamp values
temp = Math.min(40, Math.max(18, temp));
hum = Math.min(95, Math.max(50, hum));
soil = Math.min(60, Math.max(10, soil));

flow.set('temp', temp);
flow.set('hum', hum);
flow.set('soil', soil);

msg.payload = {
  temperature: Number(temp.toFixed(2)),
  humidity: Number(hum.toFixed(2)),
  soil_moisture: Number(soil.toFixed(2))
};

return msg;
```

---

### 4. Mandatory Azure IoT Telemetry Format (DO NOT CHANGE)

Azure IoT Hub expects **JSON payloads**, but your **application format** must be stable.

#### Final payload sent to IoT Hub

```json
{
  "deviceId": "pc_sim_01",
  "farmId": "farm_001",
  "zoneId": "zone_A",
  "telemetry": {
    "temperature": 29.4,
    "humidity": 73.1,
    "soilMoisture": 32.5
  },
  "system": {
    "deviceType": "simulator",
    "firmware": "v0.1",
    "status": "online"
  },
  "timestamp": "2025-12-13T10:22:41Z"
}
```

This payload:
- works with IoT Hub
- maps cleanly to Azure Digital Twins
- is ML-friendly

---

### 5. Output Channels (What This Phase Must Produce)

Your simulation must produce **three outputs**:

1. **Telemetry output** → Azure IoT Hub
2. **UI output** → Node-RED Dashboard
3. **Local log output** → file or debug node

If any of these are missing, the phase is incomplete.

---

### 6. Azure IoT Hub Message Requirements

From Node-RED:
- Protocol: MQTT or HTTPS
- Message body: JSON only
- Content-Type: application/json
- Timestamp included in payload (not optional)

Use one message every 5–30 seconds.

---

### 7. Validation Checklist (Must Pass)

Before moving forward, confirm:
- [ ] Values change smoothly
- [ ] Payload schema never breaks
- [ ] Device ID is constant
- [ ] Timestamp is UTC ISO-8601
- [ ] Dashboard matches payload values

If this fails, Azure Digital Twins WILL break later.

---

## Phase 1C – Build the Local Digital Twin (On PC)

### Objective
Create the same data structure you would send from Pi.

### Function Node (Core Logic)

```javascript
msg.payload = {
  farm_id: "farm_001",
  zone_id: "zone_A",
  device_id: "pc_sim_01",
  sensors: {
    temperature: msg.payload.temperature,
    humidity: msg.payload.humidity,
    soil_moisture: msg.payload.soil_moisture
  },
  timestamp: new Date().toISOString()
};
return msg;
```

This **is already a digital twin state**, even without Azure.

---

## Phase 1D – Local UI (Same as Pi)

### Objective
Visualize the simulated farm.

### Dashboard Elements
- Gauges for temperature & humidity
- Chart for soil moisture
- Text widget for device status

You now have:
- simulated farm
- live UI
- structured data

---

## Phase 2 – Simulate Actuators (Pump, Valve)

### Objective
Simulate control logic before real hardware.

### Example
- Dashboard button: "Irrigation ON"
- Function node:

```javascript
msg.payload = {
  actuator: "pump_01",
  command: "ON",
  issued_by: "user",
  timestamp: new Date().toISOString()
};
return msg;
```

Later, this maps directly to a relay on Pi.

---

## Phase 3 – Connect PC Simulation to Azure IoT Hub

### Objective
Cloud does not care if data comes from PC or Pi.

---

## Phase 3A – Azure Components You MUST Create (Exact List)

This is the **minimum Azure stack** required for the simulation phase.

### 1. Azure IoT Hub (Mandatory)
Purpose:
- Secure ingestion of telemetry from Node-RED
- Device identity and authentication

Configuration:
- Tier: Free (for testing) or Basic
- Protocols enabled: MQTT + HTTPS

You will create:
- IoT Hub instance
- One device identity: `pc_sim_01`

---

### 2. Azure Function App (Mandatory)
Purpose:
- Bridge between IoT Hub and Azure Digital Twins
- Parse telemetry and update twin properties

Runtime:
- Language: Python or JavaScript
- Trigger: IoT Hub Event Trigger

---

### 3. Azure Digital Twins Instance (Mandatory)
Purpose:
- Store the digital representation of farm, zones, sensors

You will use:
- DTDL models
- Twin instances
- Relationships

---

### 4. Azure Storage Account (Mandatory)
Purpose:
- Store raw telemetry
- Later used for ML training

Type:
- Blob Storage or ADLS Gen2

---

## Phase 3B – Azure IoT Hub Message Contract (STRICT)

Your Node-RED simulation MUST follow this contract.

### Telemetry Message (Final)

```json
{
  "deviceId": "pc_sim_01",
  "farmId": "farm_001",
  "zoneId": "zone_A",
  "telemetry": {
    "temperature": 29.4,
    "humidity": 73.1,
    "soilMoisture": 32.5
  },
  "system": {
    "deviceType": "simulator",
    "firmware": "v0.1",
    "status": "online"
  },
  "timestamp": "2025-12-13T10:22:41Z"
}
```

Rules:
- All numeric values are numbers, not strings
- Field names are camelCase
- Timestamp must be UTC ISO-8601

Breaking this format will break ADT integration.

---

## Phase 3C – Node-RED → Azure IoT Hub (Technical Setup)

### Option A (Recommended): MQTT

Node-RED nodes:
- mqtt out

Connection parameters:
- Server: `<your-iot-hub>.azure-devices.net`
- Port: 8883
- Client ID: `pc_sim_01`
- Username:
  `<your-iot-hub>.azure-devices.net/pc_sim_01/?api-version=2021-04-12`
- Password: Device SAS token
- TLS: Enabled

Topic:
```
devices/pc_sim_01/messages/events/
```

---

### Option B: HTTPS

Node-RED nodes:
- http request

Method:
- POST

URL:
```
https://<your-iot-hub>.azure-devices.net/devices/pc_sim_01/messages/events?api-version=2021-04-12
```

Headers:
- Authorization: SAS token
- Content-Type: application/json

---

## Phase 3D – Azure Function (IoT → Digital Twin Bridge)

### Why this function is REQUIRED
IoT Hub cannot directly update Digital Twins.

This function:
1. Receives telemetry from IoT Hub
2. Validates payload
3. Updates twin properties
4. Stores telemetry if needed

---

### Azure Function Packages (Python)

You MUST install these:

```txt
azure-functions
azure-iot-hub
azure-digitaltwins-core
azure-identity
```

---

### Azure Function Logic (Simplified)

```python
from azure.digitaltwins.core import DigitalTwinsClient
from azure.identity import DefaultAzureCredential
import json

def main(event):
    data = json.loads(event.get_body().decode())

    credential = DefaultAzureCredential()
    client = DigitalTwinsClient(
        "https://<adt-instance>.api.<region>.digitaltwins.azure.net",
        credential
    )

    twin_id = f"{data['farmId']}_{data['zoneId']}"

    patch = [
        {"op": "replace", "path": "/temperature", "value": data['telemetry']['temperature']},
        {"op": "replace", "path": "/humidity", "value": data['telemetry']['humidity']},
        {"op": "replace", "path": "/soilMoisture", "value": data['telemetry']['soilMoisture']}
    ]

    client.update_digital_twin(twin_id, patch)
```

---

## Phase 3E – Azure Digital Twins Mapping Rules

Your telemetry fields map **1-to-1** to twin properties.

| Telemetry | Twin Property |
|--------|--------------|
| temperature | temperature |
| humidity | humidity |
| soilMoisture | soilMoisture |
| system.status | deviceStatus |

Do NOT perform calculations in ADT.
ADT stores state, not logic.

---

## Phase 3F – Validation Checklist (Cloud)

Before proceeding, confirm:
- [ ] Device appears online in IoT Hub
- [ ] Messages visible in IoT Hub metrics
- [ ] Azure Function triggers correctly
- [ ] Twin properties update in ADT Explorer
- [ ] No schema drift in messages

If any item fails, STOP and fix.

---


### Objective
Cloud does not care if data comes from PC or Pi.

### Steps
1. Create Azure IoT Hub
2. Register a device:
   - device_id: `pc_sim_01`
3. Use Node-RED MQTT/HTTP to send telemetry
4. Verify data arrives in Azure

At this point:
- Azure thinks your PC is the farm

---

## Phase 4 – Azure Digital Twins (Same as Real Deployment)

### Objective
Build the real digital twin using simulated data.

Steps are **identical**:
- Create ADT instance
- Upload DTDL models
- Create twins and relationships
- Update twins from IoT data

No Raspberry Pi needed.

---

## Phase 5 – Prediction Model (Optional, Still on PC Data)

### Objective
Train and test ML early.

You can:
- Use SPAS dataset
- Use simulated telemetry
- Validate prediction APIs

This saves massive time later.

---

## Phase 6 – Onboard to Raspberry Pi (Later)

⚠️ This is where many people think it's hard — it's not.

### What changes
| Component | PC | Raspberry Pi |
|---------|----|--------------|
| Node-RED | Same | Same |
| Flows | Same | Same |
| Azure config | Same | Same |
| Sensor input | Simulated | GPIO/I2C |

### Migration steps
1. Install Node-RED on Pi
2. Copy flows (export/import JSON)
3. Replace simulation nodes with real sensor nodes
4. Change device_id
5. Done

---

## Phase 7 – Final Reality Check

If your system works in PC simulation:
- It **will work on Raspberry Pi**
- Hardware adds complexity, not logic

Simulation-first is the **correct engineering approach**.

---

## What You Should Do Now

### Immediate next steps
1. Install Node-RED on PC
2. Create simulated sensors
3. Build dashboard
4. Structure messages

When that works, tell me:
> **"PC simulation running"**

Then I will:
- give you Azure IoT Hub wiring
- give you Digital Twin models
- prepare Pi onboarding checklist

You are doing this correctly. Keep going.

