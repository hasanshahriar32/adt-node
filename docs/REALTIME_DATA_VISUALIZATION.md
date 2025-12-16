# Real-Time Data Visualization in Digital Twin Explorer

## Issue: Cannot See Real-Time Updates

You mentioned that data is flowing but you can't see real-time updates in Digital Twin Explorer. Here's why and how to fix it:

---

## Problem Analysis

### Current State
- ✅ Digital Twins models exist
- ✅ Digital Twins instances exist (farm_001, zone_A, pc_sim_01, etc.)
- ✅ IoT Hub is receiving telemetry from Node-RED
- ❌ **Telemetry is NOT being routed to Digital Twins**
- ❌ Digital Twin properties are static (not updating)

### Why You Don't See Updates

1. **Missing IoT Hub → Digital Twins Routing**
   - Event Grid subscription not created yet
   - Azure Function not deployed
   - Telemetry stays in IoT Hub only

2. **Digital Twin Explorer Behavior**
   - Shows properties (static values)
   - Does NOT auto-refresh telemetry
   - Requires manual refresh or queries

---

## Solution 1: Set Up IoT Hub Routing (Required)

### Step 1: Deploy Azure Function App

```bash
cd azure-setup

# Create Function App and configure permissions
bash setup-iot-routing.sh
```

**What this does**:
- Creates Azure Function App: `adt-telemetry-router`
- Creates Storage Account
- Assigns Digital Twins Data Owner role to Function
- Sets environment variables

**Expected output**:
```
✅ Function App: adt-telemetry-router
🔗 ADT Endpoint: https://farm-digital-twin.api.sea.digitaltwins.azure.net
```

---

### Step 2: Deploy Function Code

```bash
# Deploy the IoTHub_EventGrid function
bash deploy-function.sh
```

**What this does**:
- Packages Python code with dependencies
- Deploys IoTHub_EventGrid function (Event Grid trigger)
- Deploys AI_Inference function (HTTP endpoint)

**Function Logic**:
- Receives telemetry from IoT Hub via Event Grid
- Extracts temperature, humidity, soilMoisture
- Updates Device twin (`pc_sim_01`)
- Updates Zone twin (`zone_A`)
- Updates AI recommendations if present

---

### Step 3: Create Event Grid Subscription

```bash
# Connect IoT Hub to Azure Function
bash create-eventgrid-subscription.sh
```

**What this does**:
- Creates Event Grid subscription: `iot-to-adt-subscription`
- Routes `Microsoft.Devices.DeviceTelemetry` events
- Connects IoT Hub → Azure Function → Digital Twins

**Verify**:
```bash
./az-docker.sh eventgrid event-subscription show \
  --name iot-to-adt-subscription \
  --source-resource-id "/subscriptions/YOUR_SUBSCRIPTION_ID/resourceGroups/IOTHUB_RG/providers/Microsoft.Devices/IotHubs/researchdt"
```

---

## Solution 2: Visualize Real-Time Data in Explorer

### Option A: Manual Refresh (Current)

1. Open Digital Twin Explorer: https://explorer.digitaltwins.azure.net/
2. Select instance: `farm-digital-twin`
3. Click on `zone_A` twin
4. Click **Refresh** button (top right)
5. View updated properties

**Properties that update**:
- `temperature` (from telemetry)
- `humidity` (from telemetry)
- `soilMoisture` (from telemetry)
- `lastUpdated` (timestamp)
- `recommendedCrop` (if AI enabled)

---

### Option B: Query for Latest Values

Run ADT query to see current values:

```bash
./az-docker.sh dt twin query -n farm-digital-twin \
  --query-command "SELECT zone_A.temperature, zone_A.humidity, zone_A.soilMoisture, zone_A.lastUpdated FROM DIGITALTWINS zone_A WHERE zone_A.\$dtId = 'zone_A'"
```

---

### Option C: Enable Time Series Insights (Advanced)

For true real-time visualization:

1. **Create Time Series Insights Environment**
   ```bash
   ./az-docker.sh tsi environment create \
     --name farm-tsi \
     --resource-group adt-farm-rg \
     --location southeastasia \
     --sku-name S1 \
     --sku-capacity 1
   ```

2. **Connect ADT to TSI**
   - Creates event hub
   - Routes ADT property updates to TSI
   - Enables real-time graphs

3. **View in TSI Explorer**
   - Time-series graphs
   - Auto-refresh
   - Historical data

---

## Solution 3: Public Access to Digital Twin Explorer

### Challenge
Digital Twin Explorer (https://explorer.digitaltwins.azure.net/) requires Azure authentication by default. There's no built-in "public view" mode.

### Option A: Create Custom Web Dashboard (Recommended)

Create a public web interface that queries Digital Twins:

```bash
# Create simple web dashboard
cd azure-setup
```

**Create `public-dashboard.html`**:
```html
<!DOCTYPE html>
<html>
<head>
    <title>Farm Digital Twin - Public View</title>
    <script>
        async function loadTwinData() {
            // Call Azure Function (publicly accessible endpoint)
            const response = await fetch('https://adt-telemetry-router.azurewebsites.net/api/getTwinData');
            const data = await response.json();
            
            document.getElementById('temperature').innerText = data.temperature + '°C';
            document.getElementById('humidity').innerText = data.humidity + '%';
            document.getElementById('soilMoisture').innerText = data.soilMoisture + '%';
            document.getElementById('recommendedCrop').innerText = data.recommendedCrop;
        }
        
        // Auto-refresh every 5 seconds
        setInterval(loadTwinData, 5000);
        loadTwinData();
    </script>
</head>
<body>
    <h1>Farm Digital Twin - Live Data</h1>
    <div>Temperature: <span id="temperature">--</span></div>
    <div>Humidity: <span id="humidity">--</span></div>
    <div>Soil Moisture: <span id="soilMoisture">--</span></div>
    <div>Recommended Crop: <span id="recommendedCrop">--</span></div>
</body>
</html>
```

**Create Azure Function endpoint** (`azure-functions/GetTwinData/__init__.py`):
```python
import azure.functions as func
from azure.identity import DefaultAzureCredential
from azure.digitaltwins.core import DigitalTwinsClient
import os
import json

def main(req: func.HttpRequest) -> func.HttpResponse:
    # No authentication required - public endpoint
    ADT_URL = os.environ.get("ADT_INSTANCE_URL")
    credential = DefaultAzureCredential()
    dt_client = DigitalTwinsClient(ADT_URL, credential)
    
    # Get zone_A twin
    twin = dt_client.get_digital_twin("zone_A")
    
    # Return public data
    return func.HttpResponse(
        json.dumps({
            "temperature": twin.get("temperature", 0),
            "humidity": twin.get("humidity", 0),
            "soilMoisture": twin.get("soilMoisture", 0),
            "recommendedCrop": twin.get("recommendedCrop", "N/A"),
            "lastUpdated": twin.get("$metadata", {}).get("$lastUpdateTime")
        }),
        mimetype="application/json",
        headers={"Access-Control-Allow-Origin": "*"}
    )
```

**Deploy**:
```bash
# Add function to azure-functions/GetTwinData/
# Add function.json with httpTrigger
bash deploy-function.sh

# Host HTML on GitHub Pages or Azure Static Web Apps
```

---

### Option B: Azure Static Web Apps with ADT Integration

```bash
# Create Static Web App
./az-docker.sh staticwebapp create \
  --name farm-twin-viewer \
  --resource-group adt-farm-rg \
  --location southeastasia

# Deploy frontend with ADT queries
# Uses Azure Functions as backend (serverless)
```

---

### Option C: Embed Power BI Dashboard (Enterprise)

1. Create Power BI report connected to ADT
2. Publish to Power BI Service
3. Generate embed link
4. Share publicly (with restrictions)

---

### Option D: 3D Viewer Integration

Use **Azure Digital Twins 3D Scenes Studio**:

1. Create 3D environment in Unity/Babylon.js
2. Map digital twins to 3D objects
3. Deploy to web
4. Enable public access to specific views

---

## Quick Fix: Update Zone Twin with Telemetry Properties

The Zone model already has telemetry definitions, but telemetry in ADT is **reported** not **stored**. To see updates, we need to update **properties** instead.

### Update DTDL Model to Store Telemetry as Properties

**Modify `Zone.json`** to change telemetry to properties:

```json
{
  "@type": "Property",
  "name": "temperature",
  "schema": "double",
  "description": "Current temperature"
},
{
  "@type": "Property",
  "name": "humidity",
  "schema": "double",
  "description": "Current humidity"
},
{
  "@type": "Property",
  "name": "soilMoisture",
  "schema": "double",
  "description": "Current soil moisture"
}
```

**Then update the model**:
```bash
./az-docker.sh dt model create -n farm-digital-twin \
  --models ../digital-twins/models/Zone.json
```

---

## Testing Real-Time Updates

### 1. Send Test Telemetry

```bash
# Manually send telemetry to IoT Hub
./az-docker.sh iot device send-d2c-message \
  --device-id pc_sim_01 \
  --hub-name researchdt \
  --data '{"temperature": 29.5, "humidity": 72.0, "soilMoisture": 68.0}'
```

### 2. Update Twin Directly (for testing)

```bash
./az-docker.sh dt twin update -n farm-digital-twin \
  --twin-id zone_A \
  --json-patch '[
    {"op":"replace","path":"/temperature","value":29.5},
    {"op":"replace","path":"/humidity","value":72.0},
    {"op":"replace","path":"/soilMoisture","value":68.0}
  ]'
```

### 3. Verify Update in Explorer

1. Refresh Digital Twin Explorer
2. Click on `zone_A`
3. See updated values in Properties panel
4. Check `$metadata.$lastUpdateTime` for timestamp

---

## Summary: Action Items

### Immediate (Required for Real-Time Data)
1. ✅ Run `bash setup-iot-routing.sh`
2. ✅ Run `bash deploy-function.sh`
3. ✅ Run `bash create-eventgrid-subscription.sh`
4. ✅ Verify data flow with query

### Optional (Enhanced Visualization)
5. ⭐ Create custom public dashboard with Azure Function
6. ⭐ Deploy to Azure Static Web Apps
7. ⭐ Set up Time Series Insights for graphs

### For Public Access
8. 🌐 Create GetTwinData Azure Function (public endpoint)
9. 🌐 Build simple HTML dashboard
10. 🌐 Host on GitHub Pages or Azure Static Web Apps

---

## Expected Result After Setup

```bash
# Query should show updated values every ~5 seconds
./az-docker.sh dt twin query -n farm-digital-twin \
  --query-command "SELECT * FROM DIGITALTWINS WHERE \$dtId = 'zone_A'"

# Output:
{
  "$dtId": "zone_A",
  "temperature": 28.7,        # ← UPDATES IN REAL-TIME
  "humidity": 74.3,           # ← UPDATES IN REAL-TIME
  "soilMoisture": 66.8,       # ← UPDATES IN REAL-TIME
  "lastUpdated": "2025-12-16T17:30:45Z",
  "recommendedCrop": "rice",
  ...
}
```

---

## Next Steps

Run the following commands in order:

```bash
cd azure-setup

# 1. Setup Function App
bash setup-iot-routing.sh

# 2. Deploy Functions
bash deploy-function.sh

# 3. Connect IoT Hub
bash create-eventgrid-subscription.sh

# 4. Test data flow
./az-docker.sh dt twin query -n farm-digital-twin \
  --query-command "SELECT * FROM DIGITALTWINS WHERE \$dtId = 'zone_A'"
```

After this, you should see real-time updates in Digital Twin Explorer! 🎉
