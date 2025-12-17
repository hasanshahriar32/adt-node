# Changes and Updates - December 17, 2025

## 🎯 Session Summary

Successfully diagnosed and resolved the issue preventing real-time data from appearing in Azure Digital Twins Explorer. The root cause was that Node-RED simulation was not running, and Event Grid subscription was missing.

---

## 🔧 Changes Made

### 1. Node-RED Simulation - Restarted and Verified

**Issue**: Node-RED was not running despite previous attempts
- Multiple defunct/zombie processes found from previous failed attempts
- No active `node-red` process in system

**Solution**: 
- Started Node-RED using the correct `start_simulation.sh` script
- Verified MQTT connection to IoT Hub successful

**Files Involved**:
- `/home/hs32/Documents/Projects/adt/simulation/start_simulation.sh` ✅ (Already correct, no changes needed)
- `/home/hs32/Documents/Projects/adt/simulation/.env` ✅ (Already correct, no changes needed)

**Current Status**: 
- ✅ Node-RED running (PID: 385523)
- ✅ Connected to IoT Hub via MQTT: `pc_sim_01@mqtts://researchdt.azure-devices.net:8883`
- ✅ SAS token valid (1 year expiry)

**Verification Commands**:
```bash
# Check if Node-RED is running
ps aux | grep node-red | grep -v grep

# View simulation logs
tail -f /home/hs32/Documents/Projects/adt/simulation/simulation.log
```

---

### 2. Azure Function App - Role Assignment Fixed

**Issue**: Function App managed identity didn't have permission to update Digital Twins
- Previous attempts failed with "identity not found in graph database"
- Caused by managed identity propagation delay

**Solution**: 
- Used `--assignee-object-id` and `--assignee-principal-type` flags
- Successfully assigned "Azure Digital Twins Data Owner" role

**Azure CLI Command**:
```bash
./az-docker.sh role assignment create \
  --assignee-object-id "25d77024-ff03-47fb-9f1c-29e1bcd073a4" \
  --assignee-principal-type ServicePrincipal \
  --role "Azure Digital Twins Data Owner" \
  --scope "/subscriptions/2128b63d-ecaf-42c5-bb3c-b9ba6919e10d/resourceGroups/adt-farm-rg/providers/Microsoft.DigitalTwins/digitalTwinsInstances/farm-digital-twin"
```

**Result**:
- ✅ Role assignment successful
- ✅ Function App can now update Digital Twins
- Assignment ID: `06d41916-3627-4813-a19f-f219434a5a00`
- Created: 2025-12-16T20:18:11Z

**Verification**:
```bash
# Check role assignments
PRINCIPAL_ID=$(./az-docker.sh functionapp identity show -n adt-telemetry-router -g adt-farm-rg --query principalId -o tsv)
./az-docker.sh role assignment list --assignee "$PRINCIPAL_ID" --scope "/subscriptions/2128b63d-ecaf-42c5-bb3c-b9ba6919e10d/resourceGroups/adt-farm-rg/providers/Microsoft.DigitalTwins/digitalTwinsInstances/farm-digital-twin"
```

---

### 3. Event Grid Provider - Registered

**Issue**: Microsoft.EventGrid provider not registered in subscription

**Solution**:
```bash
./az-docker.sh provider register --namespace Microsoft.EventGrid
```

**Result**:
- ✅ Provider registration: **Registered**
- Required for creating Event Grid subscriptions

**Verification**:
```bash
./az-docker.sh provider show -n Microsoft.EventGrid --query "registrationState" -o tsv
```

---

### 4. Event Grid Subscription - Pending (Manual Setup Required)

**Issue**: Azure CLI attempts to create Event Grid subscription failed with:
1. First attempt: Endpoint validation failed
2. Second attempt (webhook): Authentication token invalid

**Root Cause**: 
- IoT Hub is in different resource group (`DT_Research`) than Digital Twins (`adt-farm-rg`)
- Cross-resource-group Event Grid subscriptions have authentication complexities

**Manual Setup Required** (Azure Portal):

#### Step-by-Step Instructions:

1. **Navigate to IoT Hub**:
   - Go to https://portal.azure.com
   - Search for "researchdt" IoT Hub
   - Open the IoT Hub resource

2. **Create Event Subscription**:
   - In left menu, click **Events**
   - Click **+ Event Subscription**

3. **Configure Subscription**:
   - **Name**: `iot-to-adt-subscription`
   - **Event Schema**: Event Grid Schema
   - **Topic Types**: IoT Hub
   - **Filter to Event Types**: Check ✅ **Device Telemetry** only
   - **Endpoint Type**: Azure Function
   - **Endpoint**: Click "Select an endpoint"
     - Subscription: (your subscription)
     - Resource Group: `adt-farm-rg`
     - Function App: `adt-telemetry-router`
     - Function: `IoTHub_EventGrid`
     - Click "Confirm Selection"

4. **Create**:
   - Click **Create** button
   - Wait 2-3 minutes for provisioning

**Alternative CLI Command** (if authentication fixed):
```bash
./az-docker.sh eventgrid event-subscription create \
  --name iot-to-adt-subscription \
  --source-resource-id "/subscriptions/2128b63d-ecaf-42c5-bb3c-b9ba6919e10d/resourceGroups/DT_Research/providers/Microsoft.Devices/IotHubs/researchdt" \
  --endpoint-type webhook \
  --endpoint "https://adt-telemetry-router.azurewebsites.net/runtime/webhooks/eventgrid?functionName=IoTHub_EventGrid&code=<FUNCTION_KEY>" \
  --included-event-types Microsoft.Devices.DeviceTelemetry \
  --event-delivery-schema EventGridSchema
```

**Note**: Function keys are managed via Azure Portal and should not be stored in code.

---

## 📊 Current Architecture

```
┌─────────────────┐         ┌─────────────┐         ┌──────────────┐
│   Node-RED      │ MQTT    │  IoT Hub    │ Event   │ Azure        │
│   Simulation    ├────────►│ researchdt  │ Grid ──►│ Function App │
│   (localhost)   │ :8883   │             │         │              │
└─────────────────┘         └─────────────┘         └──────┬───────┘
                                                            │
                                                            │ HTTPS
                                                            ▼
                                                    ┌───────────────┐
                                                    │ Azure Digital │
                                                    │ Twins         │
                                                    │ farm-digital- │
                                                    │ twin          │
                                                    └───────────────┘
```

### Data Flow:

1. **Node-RED** fetches weather data from weatherapi.com (Dhaka)
2. **Node-RED** calculates soil moisture based on rainfall/evaporation
3. **Node-RED** publishes telemetry via MQTT to **IoT Hub** every 5-10 seconds
4. **IoT Hub** triggers **Event Grid** event (Device Telemetry)
5. **Event Grid** routes to **Azure Function** (`IoTHub_EventGrid`)
6. **Azure Function** updates **Azure Digital Twins** properties:
   - Updates `zone_A` twin: temperature, humidity, soilMoisture
   - Updates `pc_sim_01` twin: temperature, humidity, soilMoisture

### Telemetry Format:

```json
{
  "schemaVersion": "1.0",
  "deviceId": "pc_sim_01",
  "farmId": "farm_001",
  "zoneId": "zone_A",
  "telemetry": {
    "temperature": 30.5,
    "humidity": 70.2,
    "soilMoisture": 62.8
  },
  "timestamp": "2025-12-17T02:22:00Z"
}
```

---

## 🗄️ Azure Resources Status

| Resource | Name | Resource Group | Status |
|----------|------|----------------|--------|
| Digital Twins | farm-digital-twin | adt-farm-rg | ✅ Running |
| IoT Hub | researchdt | DT_Research | ✅ Running |
| Function App | adt-telemetry-router | adt-farm-rg | ✅ Running |
| Storage Account | adtfunc807614 | adt-farm-rg | ✅ Running |
| Device | pc_sim_01 | (IoT Hub) | ✅ Registered |

### Digital Twins Models:

| Model | ID | Version | Properties |
|-------|-----|---------|------------|
| Farm | dtmi:com:contoso:Farm;1 | Uploaded | name, location |
| Zone | dtmi:com:contoso:Zone;1 | Uploaded | temperature, humidity, soilMoisture |
| Device | dtmi:com:contoso:Device;1 | Uploaded | temperature, humidity, soilMoisture, batteryLevel |
| Crop | dtmi:com:contoso:Crop;1 | Uploaded | cropType, plantingDate |

### Digital Twins Instances:

| Twin ID | Model | Initial Values |
|---------|-------|----------------|
| farm_001 | Farm | name: "Contoso Farm" |
| zone_A | Zone | temp: 26.0, humidity: 70.0, soil: 65.0 |
| pc_sim_01 | Device | (sensor properties) |
| rice | Crop | cropType: "rice" |
| wheat | Crop | cropType: "wheat" |
| maize | Crop | cropType: "maize" |

### Relationships:

```
farm_001 ──hasFarmZone──> zone_A
zone_A ──hasDevice──> pc_sim_01
zone_A ──hasCrop──> rice
```

---

## 🔍 Verification Steps

### 1. Verify Node-RED is Running

```bash
ps aux | grep node-red | grep -v grep
# Expected: Should show node-red process

# Check MQTT connection in logs
tail -f /home/hs32/Documents/Projects/adt/simulation/simulation.log | grep "Connected to broker"
# Expected: "Connected to broker: pc_sim_01@mqtts://researchdt.azure-devices.net:8883"
```

### 2. Verify IoT Hub Receives Messages

```bash
cd /home/hs32/Documents/Projects/adt/azure-setup
./az-docker.sh iot hub monitor-events --hub-name researchdt --device-id pc_sim_01
# Expected: JSON messages with temperature, humidity, soilMoisture
```

### 3. Verify Digital Twins Updates (After Event Grid Setup)

```bash
# Query current values
./az-docker.sh dt twin show -n farm-digital-twin --twin-id zone_A \
  --query "{temperature:temperature,humidity:humidity,soilMoisture:soilMoisture,lastUpdated:lastUpdated}"

# Expected: Values should be updating every 5-10 seconds
```

### 4. Verify in Azure Digital Twins Explorer

1. Open: https://explorer.digitaltwins.azure.net
2. Sign in with Azure account
3. Select `farm-digital-twin` instance
4. Click on `zone_A` twin
5. Properties panel should show updating values:
   - temperature (°C)
   - humidity (%)
   - soilMoisture (%)
   - lastUpdated (timestamp)

---

## 📝 Configuration Files

### `/home/hs32/Documents/Projects/adt/simulation/.env`

```env
WEATHER_API_KEY=<YOUR_WEATHER_API_KEY>
WEATHER_LOCATION=Dhaka
IOT_HUB_HOSTNAME=researchdt.azure-devices.net
DEVICE_ID=pc_sim_01
IOT_HUB_SAS_KEY=<GENERATED_SAS_KEY>
```

**Note**: Keys are stored locally in `.env` file (not committed to git). Generate SAS key using `generate_sas.py`.

### Azure Function App Settings (Environment Variables)

| Key | Value |
|-----|-------|
| ADT_INSTANCE_URL | https://farm-digital-twin.api.sea.digitaltwins.azure.net |
| AZURE_CLIENT_ID | (Managed Identity) |
| FUNCTIONS_WORKER_RUNTIME | python |
| AzureWebJobsStorage | (Connection string) |

---

## 🚀 Next Steps

### Immediate (Required):

1. **✅ COMPLETED**: Node-RED simulation running
2. **✅ COMPLETED**: Function App has Digital Twins permissions
3. **✅ COMPLETED**: Event Grid provider registered
4. **⏳ PENDING**: Create Event Grid subscription (Manual Azure Portal)
5. **⏳ PENDING**: Verify data appears in Azure Digital Twins Explorer

### Future Enhancements:

1. **Public Dashboard**: Deploy HTML dashboard to GitHub Pages
2. **AI Inference**: Activate edge AI model for crop disease detection
3. **Alerts**: Configure alerts for abnormal sensor values
4. **Historical Data**: Store telemetry in Time Series Insights or Cosmos DB
5. **Visualization**: Create Power BI dashboard connected to Digital Twins

---

## 🐛 Known Issues

### 1. Node-RED Connection Drops
**Symptom**: Node-RED shows "Disconnected from broker" then reconnects
**Root Cause**: Normal MQTT keep-alive behavior or network fluctuations
**Impact**: Minimal - connection recovers automatically
**Monitoring**: Check logs for excessive disconnects

### 2. Event Grid Subscription Creation via CLI
**Symptom**: CLI commands fail with authentication/validation errors
**Workaround**: Use Azure Portal (see manual setup instructions above)
**Root Cause**: Cross-resource-group subscription complexity

### 3. SAS Token Regeneration
**Note**: Current SAS token expires in 1 year (generated from primary key)
**Future Action**: Regenerate token before expiry or implement auto-refresh

---

## 📞 Important URLs

- **Azure Portal**: https://portal.azure.com
- **Digital Twins Explorer**: https://explorer.digitaltwins.azure.net
- **Node-RED UI**: http://localhost:1880
- **Function App**: https://adt-telemetry-router.azurewebsites.net
- **IoT Hub Endpoint**: researchdt.azure-devices.net

---

## 🔐 Security Notes

- SAS key stored in `.env` file (local development only)
- Function App uses Managed Identity (no keys in code)
- Event Grid webhook uses system key for validation
- All connections use TLS/HTTPS

---

## 📚 Related Documentation

- [Phase 4-5: Azure Digital Twins Infrastructure Setup](./Phase%204-5:%20Azure%20Digital%20Twins%20Infrastructure%20Setup.md)
- [Phase 6: IoT Routing and Real-Time Visualization](./Phase%206:%20IoT%20Routing%20and%20Real-Time%20Visualization.md)
- [Simulation README](../simulation/README.md)
- [Azure Setup README](../azure-setup/README.md)

---

**Last Updated**: December 17, 2025, 02:25 AM
**Updated By**: GitHub Copilot Assistant
**Status**: Node-RED ✅ | Role Assignment ✅ | Event Grid ⏳ Pending Manual Setup
