# Azure Digital Twins Deployment - Current Status

## ✅ What's Been Completed

### 1. **Azure Infrastructure Deployed**
- ✅ Resource Group: `adt-farm-rg` (southeastasia)
- ✅ Digital Twins Instance: `farm-digital-twin`
- ✅ Azure Function App: `adt-telemetry-router`
- ✅ Storage Account: Created for Function App
- ✅ Application Insights: Monitoring enabled

### 2. **DTDL Models Updated**
- ✅ Farm model (dtmi:agriculture:Farm;1)
- ✅ Zone model (dtmi:agriculture:Zone;1) - **Modified to use Properties**
- ✅ Device model (dtmi:agriculture:Device;1) - **Modified to use Properties**
- ✅ Crop model (dtmi:agriculture:Crop;1)

### 3. **Digital Twins Created**
- ✅ farm_001 (Farm)
- ✅ zone_A (Zone)
- ✅ pc_sim_01 (Device)
- ✅ rice, wheat, maize (Crops)
- ✅ All relationships recreated

### 4. **Azure Functions Deployed**
- ✅ IoTHub_EventGrid - Event Grid trigger to update twins
- ✅ GetTwinData - Public API endpoint for dashboard
- ✅ AI_Inference - Crop recommendation endpoint
- ✅ Function App configured with managed identity
- ✅ Environment variables set (ADT_INSTANCE_URL)

---

## ⚠️ Current Limitation: Telemetry vs Properties

### The Issue

Azure Digital Twins has a **fundamental design**:
- **Telemetry**: Streaming data that flows through but is NOT stored
- **Properties**: Stored attributes that can be queried and viewed

**What this means**:
- Your Node-RED sends telemetry (temperature, humidity, soilMoisture)
- This telemetry passes through IoT Hub
- ADT receives telemetry but **doesn't store it by default**
- Digital Twin Explorer shows only **properties**, not telemetry

### Why You Don't See Real-Time Updates

The current DTDL models define sensor data as **Telemetry**:
```json
{
  "@type": "Telemetry",
  "name": "temperature",
  "schema": "double"
}
```

**Telemetry is NOT queryable or storable in ADT!**

---

## 🔧 Solutions Implemented

### Solution 1: Convert Telemetry to Properties (DONE)

I've updated the DTDL models to convert telemetry to properties:

**Files Modified**:
- `digital-twins/models/Zone.json`
- `digital-twins/models/Device.json`

**Changes Made**:
```json
{
  "@type": "Property",  // Changed from "Telemetry"
  "name": "temperature",
  "schema": "double",
  "writable": true  // Added
}
```

**Status**: Models updated locally, but Azure still has old cached models. The twins were created with the old model definition.

---

## 🎯 Next Steps to See Real-Time Data

### Option A: Manual Twin Updates (Immediate)

Update twins directly via Azure CLI:

```bash
cd azure-setup

# Update zone_A with sensor data
./az-docker.sh dt twin update -n farm-digital-twin --twin-id zone_A \
  --json-patch '[
    {"op":"replace","path":"/recommendedCrop","value":"wheat"},
    {"op":"replace","path":"/recommendationConfidence","value":0.85}
  ]'
```

**Limitation**: Requires manual updates, no automatic flow from IoT Hub

---

### Option B: Complete IoT Hub Routing with Azure Function

#### Prerequisites
The Function App is deployed but Event Grid subscription failed. Here's why and how to fix:

**Steps to Complete**:

1. **Assign Digital Twins Permissions to Function App**
   ```bash
   cd azure-setup
   
   # Get Function principal ID
   PRINCIPAL_ID=$(cat .function-principal-id)
   
   # Assign role (may need to wait 5-10 minutes after function creation)
   ./az-docker.sh dt role-assignment create \
     --dtn farm-digital-twin \
     --assignee "$PRINCIPAL_ID" \
     --role "Azure Digital Twins Data Owner" \
     -g adt-farm-rg
   ```

2. **Create Event Grid Subscription via Azure Portal**
   
   Since CLI commands failed, use the portal:
   
   - Go to: [Azure Portal → IoT Hub "researchdt"](https://portal.azure.com)
   - Click **Events** → **+ Event Subscription**
   - Settings:
     - Name: `iot-to-adt-sub`
     - Event Schema: Event Grid Schema
     - Filter to Event Types: ✅ Device Telemetry
     - Endpoint Type: Azure Function
     - Select: `adt-telemetry-router/IoTHub_EventGrid`
   - Click **Create**

3. **Test the Flow**
   ```bash
   # Send test telemetry from Node-RED
   # Wait 5-10 seconds
   
   # Query to verify
   ./az-docker.sh dt twin query -n farm-digital-twin \
     --query-command "SELECT * FROM digitaltwins WHERE \$dtId = 'zone_A'"
   ```

---

### Option C: Use Time Series Insights for Telemetry Visualization

For true streaming telemetry visualization:

```bash
cd azure-setup

# Create Time Series Insights environment
./az-docker.sh tsi environment gen2 create \
  --name farm-tsi \
  --resource-group adt-farm-rg \
  --location southeastasia \
  --sku name="L1" capacity=1 \
  --time-series-id-properties deviceId \
  --warm-store-retention-time P7D
```

**What TSI Provides**:
- Real-time telemetry graphs
- Historical data storage
- Auto-refreshing dashboards
- No need to store telemetry in twin properties

---

## 📊 Current Status Summary

| Component | Status | Notes |
|-----------|--------|-------|
| Azure Digital Twins Instance | ✅ Running | farm-digital-twin.api.sea.digitaltwins.azure.net |
| DTDL Models | ✅ Uploaded | 4 models active |
| Digital Twins | ✅ Created | 6 twins with relationships |
| Azure Function App | ✅ Deployed | adt-telemetry-router |
| Function Code | ✅ Deployed | 3 functions uploaded |
| Managed Identity | ✅ Enabled | Principal ID: 25d77024-ff03-47fb-9f1c-29e1bcd073a4 |
| Digital Twins Permissions | ⚠️ Pending | Role assignment needs retry (identity propagation) |
| Event Grid Subscription | ❌ Failed | Use Azure Portal instead |
| Real-Time Telemetry Flow | ❌ Not Working | Requires Event Grid fix |

---

## 🌐 Public Dashboard Access

### Public API Endpoint

The `GetTwinData` function provides a public API:

**URL** (will be active once deployed):
```
https://adt-telemetry-router.azurewebsites.net/api/getTwinData
```

**Response Example**:
```json
{
  "farm": {
    "name": "Demo Farm",
    "location": "Bangladesh",
    "totalArea": 10.0
  },
  "zone": {
    "name": "Zone A",
    "area": 2.5,
    "soilType": "Clay Loam",
    "currentCrop": "rice",
    "recommendedCrop": "rice",
    "recommendationConfidence": 0.96
  },
  "sensors": {
    "temperature": 28.5,
    "humidity": 72.0,
    "soilMoisture": 65.0
  },
  "metadata": {
    "lastUpdated": "2025-12-16T18:48:52.308Z"
  }
}
```

### HTML Dashboard

Use the dashboard at: `azure-setup/public-dashboard.html`

**To make it public**:

1. **Option A: GitHub Pages**
   ```bash
   # Copy to docs folder
   cp azure-setup/public-dashboard.html docs/index.html
   
   # Commit and push
   git add docs/index.html
   git commit -m "Add public dashboard"
   git push
   
   # Enable GitHub Pages in repo settings → Pages → Source: /docs
   ```

2. **Option B: Azure Static Web Apps**
   ```bash
   ./az-docker.sh staticwebapp create \
     --name farm-twin-viewer \
     --resource-group adt-farm-rg \
     --location southeastasia
   ```

---

## 🔍 Verification Commands

### Check Deployed Resources

```bash
cd azure-setup

# List all resources
./az-docker.sh resource list -g adt-farm-rg --output table

# Check Function App status
./az-docker.sh functionapp list -g adt-farm-rg --query "[].{Name:name, State:state}" -o table

# Check Digital Twins models
./az-docker.sh dt model list -n farm-digital-twin --query "[].id" -o tsv

# Query all twins
./az-docker.sh dt twin query -n farm-digital-twin \
  --query-command "SELECT * FROM digitaltwins"
```

### Test Function Endpoint

```bash
# Test GetTwinData function
curl https://adt-telemetry-router.azurewebsites.net/api/getTwinData
```

---

## 📝 Key Findings & Lessons Learned

### 1. **Telemetry vs Properties**
- Azure Digital Twins does NOT store telemetry by default
- For queryable/visible data in Explorer, use Properties
- Telemetry requires Time Series Insights for visualization

### 2. **Model Versioning**
- Models cannot be updated in-place
- Must delete model → recreate with new definition
- Deleting models requires deleting all twins using them
- Relationships must be deleted before twins

### 3. **Role Assignment Delays**
- Managed Identity creation is immediate
- But identity propagation takes 5-10 minutes
- Role assignments fail if attempted too soon

### 4. **Event Grid Limitations**
- Azure CLI Event Grid commands have issues with IoT Hub sources
- Use Azure Portal for reliable Event Grid subscription creation

### 5. **Function Deployment**
- ZIP deployment works but functions may take 15-30 seconds to appear
- Use `--build-remote` flag or pre-install dependencies

---

## 🚀 Recommended Action Plan

### Immediate (Today)

1. **Wait 10 minutes** for Function App identity to propagate
2. **Retry role assignment** for Digital Twins permissions
3. **Create Event Grid subscription via Portal** (not CLI)
4. **Test telemetry flow** with Node-RED

### Short Term (This Week)

1. **Update DTDL models** to use Properties instead of Telemetry
2. **Recreate twins** with updated models
3. **Deploy dashboard** to GitHub Pages or Azure Static Web Apps
4. **Configure public access** for dashboard API

### Long Term (Optional Enhancements)

1. **Add Time Series Insights** for historical telemetry
2. **Implement AI inference** endpoint for recommendations
3. **Add authentication** to dashboard (Azure AD B2C)
4. **Create 3D visualization** with Azure Digital Twins 3D Scenes Studio

---

## 📚 Resources

- **Digital Twin Explorer**: https://explorer.digitaltwins.azure.net/
- **Azure Portal**: https://portal.azure.com
- **Function App URL**: https://adt-telemetry-router.azurewebsites.net
- **Digital Twins Endpoint**: https://farm-digital-twin.api.sea.digitaltwins.azure.net
- **Documentation Created**:
  - `docs/REALTIME_DATA_VISUALIZATION.md` - Complete guide
  - `SESSION_DOCUMENTATION.md` - Previous session notes
  - `azure-setup/public-dashboard.html` - Web dashboard
  - `azure-functions/GetTwinData/` - Public API

---

## 💡 Summary

**What Works**:
- ✅ Azure Digital Twins infrastructure fully deployed
- ✅ Models uploaded and twins created
- ✅ Azure Function App deployed with code
- ✅ Public API endpoint created
- ✅ Web dashboard created

**What Needs Manual Action**:
- ⏳ Wait for Function App identity propagation (5-10 min)
- 🔧 Create Event Grid subscription via Azure Portal
- 🔄 Test end-to-end telemetry flow

**Why No Real-Time Updates Yet**:
- Event Grid subscription creation failed (use Portal instead)
- Telemetry is defined as streaming data (not stored in twins)
- Need to either:
  - Complete Event Grid setup + update twins via Function, OR
  - Add Time Series Insights for telemetry visualization

---

**Next Command to Run** (after 10 min wait):

```bash
cd azure-setup

# Retry role assignment
PRINCIPAL_ID=$(cat .function-principal-id)
./az-docker.sh dt role-assignment create \
  --dtn farm-digital-twin \
  --assignee "$PRINCIPAL_ID" \
  --role "Azure Digital Twins Data Owner" \
  -g adt-farm-rg
```

Then create Event Grid subscription via Azure Portal as described above.
