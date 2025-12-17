# 🚀 System Status - December 17, 2025

## 🎉 SYSTEM FULLY OPERATIONAL

**Last Verified**: 2025-12-17 07:35:53 UTC  
**Data Pipeline**: ✅ Working end-to-end  
**Azure Digital Twins Explorer**: ✅ Showing real-time data (60s updates)
**Event Grid**: ✅ Connected and delivering events

---

## ✅ Completed Components

### 1. Node-RED Simulation
- **Status**: ✅ Running
- **Connection**: ✅ Connected to IoT Hub via MQTT
- **Endpoint**: `pc_sim_01@mqtts://researchdt.azure-devices.net:8883`
- **Log File**: `/tmp/nodered_fresh.log`
- **Data Frequency**: Every 60 seconds (heartbeat)
- **Weather Source**: weatherapi.com (Dhaka, Bangladesh)

**Quick Check**:
```bash
ps aux | grep node-red | grep -v grep
tail -f /tmp/nodered_fresh.log
```

**Start Command**:
```bash
cd /home/hs32/Documents/Projects/adt/simulation
./start_simulation.sh
```

---

### 2. Azure IoT Hub
- **Name**: researchdt
- **Resource Group**: DT_Research
- **Location**: Central India
- **Status**: ✅ Running
- **Device**: pc_sim_01 (Enabled)
- **Endpoint**: researchdt.azure-devices.net

**Quick Check**:
```bash
cd /home/hs32/Documents/Projects/adt/azure-setup
./az-docker.sh iot hub monitor-events --hub-name researchdt --device-id pc_sim_01
```

---

### 3. Azure Digital Twins
- **Name**: farm-digital-twin
- **Resource Group**: adt-farm-rg
- **Location**: Southeast Asia
- **Status**: ✅ Running and receiving real-time updates
- **Endpoint**: farm-digital-twin.api.sea.digitaltwins.azure.net

**Models Uploaded**: 2 (Properties-based)
- Zone (dtmi:agriculture:Zone;1) - with temperature, humidity, soilMoisture **Properties**
- Device (dtmi:agriculture:Device;1) - with sensor **Properties**

**Twins Created**: 2
- zone_A (Zone twin - receiving updates ✅)
- pc_sim_01 (Device twin - receiving updates ✅)

**Last Update**:
- Temperature: 27.0°C
- Humidity: 72.0%
- Soil Moisture: 63.0%
- Timestamp: 2025-12-17T07:35:53.585Z
- **Update Frequency**: Every ~60 seconds (real-time)

**Quick Check**:
```bash
cd /home/hs32/Documents/Projects/adt/azure-setup
./az-docker.sh dt twin show -n farm-digital-twin --twin-id zone_A --query "{temperature:temperature,humidity:humidity,soilMoisture:soilMoisture,lastUpdated:lastUpdated}"
```

---

### 4. Azure Function App
- **Name**: adt-telemetry-router
- **Resource Group**: adt-farm-rg
- **Runtime**: Python 3.11
- **Status**: ✅ Running and processing events successfully
- **URL**: https://adt-telemetry-router.azurewebsites.net

**Functions Deployed**: 3
1. **IoTHub_EventGrid** - ✅ Routes IoT Hub telemetry to Digital Twins (WORKING)
2. **GetTwinData** - Public API to fetch twin data
3. **AI_Inference** - Edge AI for crop analysis (future)

**Managed Identity**: ✅ Enabled
**Role Assignment**: ✅ Azure Digital Twins Data Owner
- Principal ID: 25d77024-ff03-47fb-9f1c-29e1bcd073a4
- Assignment ID: 06d41916-3627-4813-a19f-f219434a5a00
- Created: 2025-12-16T20:18:11Z

**Critical Fixes Applied**:
- ✅ Python packages installed via `--build-remote true`
- ✅ Function signature: `func.EventGridEvent`
- ✅ Event access: `event.get_json()` and `event.event_time.isoformat()`

**Environment Variables**:
- ADT_INSTANCE_URL: https://farm-digital-twin.api.sea.digitaltwins.azure.net

**Quick Check**:
```bash
cd /home/hs32/Documents/Projects/adt/azure-setup
./az-docker.sh functionapp show -n adt-telemetry-router -g adt-farm-rg --query "{Name:name,State:state,DefaultHostName:defaultHostName}"
```

---

### 5. Event Grid
- **Provider**: ✅ Registered (Microsoft.EventGrid)
- **System Topic**: adt-sys (in DT_Research)
- **Subscription**: ✅ iothub-to-adt-function (Active)
- **Status**: ✅ Delivering events successfully
- **Provisioning State**: Succeeded

**Subscription Details**:
- **Name**: iothub-to-adt-function
- **Source**: IoT Hub System Topic (adt-sys)
- **Destination**: Azure Function (IoTHub_EventGrid)
- **Event Type**: Microsoft.Devices.DeviceTelemetry
- **Event Schema**: EventGridSchema
- **Max Events Per Batch**: 1
- **Retry Policy**: 30 attempts, 1440 minutes TTL
- **Created**: 2025-12-17 via Azure CLI

**Quick Check**:
```bash
cd /home/hs32/Documents/Projects/adt/azure-setup
./az-docker.sh eventgrid event-subscription show \
  --name iot-to-adt-subscription \
  --source-resource-id "/subscriptions/2128b63d-ecaf-42c5-bb3c-b9ba6919e10d/resourceGroups/DT_Research/providers/Microsoft.Devices/IotHubs/researchdt"
```

---

## 📊 Data Flow Status

```
┌─────────────────┐         ┌─────────────┐         ┌──────────────┐         ┌─────────────────┐
│   Node-RED      │  MQTT   │  IoT Hub    │ Event   │ Azure        │  JSON   │ Azure Digital   │
│   Simulation    ├────────►│ researchdt  │ Grid ──►│ Function App ├────────►│ Twins           │
│   ✅ Running    │ ✅ OK   │ ✅ Running  │ ✅ OK   │ ✅ Processing│ Patch   │ ✅ Updating     │
└─────────────────┘         └─────────────┘         └──────┬───────┘
                                                            │
                                                            │ HTTPS
                                                            ▼
                                                    ┌───────────────┐
                                                    │ Azure Digital │
                                                    │ Twins         │
                                                    │ ✅ Processing │
└─────────────────┘         └─────────────┘         └──────────────┘         └─────────────────┘
```

**Current State**:
- ✅ Node-RED → IoT Hub: **Working**
- ✅ IoT Hub → Function App: **Working** (Event Grid delivering)
- ✅ Function App → Digital Twins: **Working** (updating twins)

**End-to-End Test**:
```bash
# Send test message
cd /home/hs32/Documents/Projects/adt/azure-setup
./az-docker.sh iot device send-d2c-message \
  --hub-name researchdt \
  --device-id pc_sim_01 \
  --data '{"temperature":28.0,"humidity":75.0,"soilMoisture":65.0}'

# Wait 15 seconds, then check twin
sleep 15
./az-docker.sh dt twin show -n farm-digital-twin --twin-id zone_A \
  --query "{temperature:temperature,humidity:humidity,soilMoisture:soilMoisture,lastUpdated:lastUpdated}"
```

---

## 🔍 Health Checks

### Run All Checks:
```bash
cd /home/hs32/Documents/Projects/adt

# 1. Node-RED Running?
echo "=== Node-RED Status ==="
ps aux | grep node-red | grep -v grep || echo "❌ Not running - run: cd simulation && ./start_simulation.sh"

# 2. IoT Hub Reachable?
echo -e "\n=== IoT Hub Status ==="
cd azure-setup && ./az-docker.sh iot hub show --name researchdt --query "properties.state" -o tsv

# 3. Digital Twins Reachable?
echo -e "\n=== Digital Twins Status ==="
./az-docker.sh dt show -n farm-digital-twin --query "provisioningState" -o tsv

# 4. Function App Running?
echo -e "\n=== Function App Status ==="
./az-docker.sh functionapp show -n adt-telemetry-router -g adt-farm-rg --query "state" -o tsv

# 5. Event Grid Subscription?
echo -e "\n=== Event Grid Subscription ==="
./az-docker.sh eventgrid event-subscription show \
  --name iot-to-adt-subscription \
  --source-resource-id "/subscriptions/2128b63d-ecaf-42c5-bb3c-b9ba6919e10d/resourceGroups/DT_Research/providers/Microsoft.Devices/IotHubs/researchdt" \
  --query "{Name:name,ProvisioningState:provisioningState}" -o json

# 6. Check Current Twin Values
echo -e "\n=== Current Twin Data ==="
./az-docker.sh dt twin show -n farm-digital-twin --twin-id zone_A \
  --query "{temperature:temperature,humidity:humidity,soilMoisture:soilMoisture,lastUpdated:lastUpdated}"
```

---

## 🎯 Next Steps

### Phase 6: Public Dashboard & Visualization ⏭️
1. ✅ Real-time data pipeline working
2. Create public-accessible dashboard for showcase
3. Options:
   - **Option A**: Azure Digital Twins Explorer (requires login)
   - **Option B**: Custom web dashboard with public API
   - **Option C**: Power BI embedded dashboard

### Immediate Actions:
1. **View Real-Time Data** (2 minutes):
   - Open: https://explorer.digitaltwins.azure.net
   - Select: `farm-digital-twin`
   - Click: `zone_A` twin
   - Watch: Properties updating live! ✅

2. **Keep System Running**:
   ```bash
   # Ensure Node-RED stays running
   ps aux | grep node-red | grep -v grep
   
   # If not running:
   cd /home/hs32/Documents/Projects/adt/simulation
   ./start_simulation.sh
   ```

3. **Monitor Data Flow**:
   ```bash
   # Watch IoT Hub messages
   cd /home/hs32/Documents/Projects/adt/azure-setup
   ./az-docker.sh iot hub monitor-events --hub-name researchdt --device-id pc_sim_01
   
   # Watch Digital Twin updates
   watch -n 5 './az-docker.sh dt twin show -n farm-digital-twin --twin-id zone_A --query "{temperature:temperature,humidity:humidity,soilMoisture:soilMoisture,lastUpdated:lastUpdated}"'
   ```

---

## 📁 Important Files

### Configuration:
- `/home/hs32/Documents/Projects/adt/simulation/.env` - IoT Hub credentials
- `/home/hs32/Documents/Projects/adt/simulation/flows.json` - Node-RED flow template
- `/home/hs32/Documents/Projects/adt/simulation/flows_runtime.json` - Runtime flow (generated)

### Scripts:
- `/home/hs32/Documents/Projects/adt/simulation/start_simulation.sh` - Start Node-RED
- `/home/hs32/Documents/Projects/adt/simulation/generate_sas.py` - Generate SAS token
- `/home/hs32/Documents/Projects/adt/azure-setup/az-docker.sh` - Azure CLI wrapper

### Documentation:
- `/home/hs32/Documents/Projects/adt/docs/DECEMBER_17_2025_CHANGES.md` - Today's changes
- `/home/hs32/Documents/Projects/adt/MANUAL_EVENT_GRID_SETUP.md` - Setup instructions
- `/home/hs32/Documents/Projects/adt/SYSTEM_STATUS.md` - This file

### Logs:
- `/home/hs32/Documents/Projects/adt/simulation/simulation.log` - Node-RED output

---

## 📞 Quick Reference

| Component | URL/Command |
|-----------|-------------|
| Azure Portal | https://portal.azure.com |
| Digital Twins Explorer | https://explorer.digitaltwins.azure.net |
| Node-RED UI | http://localhost:1880 |
| Function App | https://adt-telemetry-router.azurewebsites.net |
| IoT Hub Hostname | researchdt.azure-devices.net |
| Monitor IoT Hub | `./az-docker.sh iot hub monitor-events --hub-name researchdt --device-id pc_sim_01` |
| Query Twin | `./az-docker.sh dt twin show -n farm-digital-twin --twin-id zone_A` |
| Restart Simulation | `cd ~/Documents/Projects/adt/simulation && ./start_simulation.sh` |

---

## 🔐 Security Info

- **SAS Key**: Stored in `.env` (expires in 1 year from generation)
- **Managed Identity**: Used by Function App (no keys in code)
- **Function Keys**: Managed via Azure Portal (not stored in code)
- **All Connections**: TLS/HTTPS encrypted

---

## 📈 Telemetry Data Points

Current telemetry being simulated:
- **Temperature**: 25-35°C (from Dhaka weather API)
- **Humidity**: 60-85% (from Dhaka weather API)
- **Soil Moisture**: 50-80% (calculated based on rainfall + evaporation)

Data sent every: **5-10 seconds**

---

**Last Updated**: December 17, 2025, 02:30 AM  
**System Health**: 🟡 Yellow (Event Grid subscription pending)  
**Next Milestone**: Event Grid setup → 🟢 Green (fully operational)
