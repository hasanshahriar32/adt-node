# 🔧 Manual Event Grid Subscription Setup

## ⚡ Quick Start - 5 Minutes

Azure CLI failed to create the Event Grid subscription due to authentication issues. Follow these steps in Azure Portal:

---

## 📋 Step-by-Step Instructions

### Step 1: Open Azure Portal
1. Go to: https://portal.azure.com
2. Sign in with your Azure account

### Step 2: Navigate to IoT Hub
1. In the search bar at the top, type: **researchdt**
2. Click on the **researchdt** IoT Hub in the results
3. Wait for the IoT Hub page to load

### Step 3: Open Events Section
1. In the left sidebar menu, scroll down to find **Events**
2. Click on **Events**
3. You should see the Events page with a button "+ Event Subscription"

### Step 4: Create Event Subscription
1. Click the **+ Event Subscription** button at the top

### Step 5: Configure Basic Settings

Fill in the form with these values:

| Field | Value |
|-------|-------|
| **Name** | `iot-to-adt-subscription` |
| **Event Schema** | Event Grid Schema |
| **System Topic Name** | (auto-generated, leave as is) |

### Step 6: Filter Event Types

In the **Event Types** section:
1. **Uncheck** all event types first
2. **Check ONLY**: ✅ **Device Telemetry**
3. Leave all others unchecked

### Step 7: Configure Endpoint

1. **Endpoint Type**: Select **Azure Function** from dropdown
2. Click **Select an endpoint** button
3. A new panel will open on the right

In the endpoint selection panel:
- **Subscription**: (Should auto-select your subscription)
- **Resource Group**: Select **adt-farm-rg**
- **Function App**: Select **adt-telemetry-router**
- **Slot**: production (default)
- **Function**: Select **IoTHub_EventGrid**

4. Click **Confirm Selection** button at the bottom

### Step 8: Create the Subscription

1. Review all settings:
   - Name: `iot-to-adt-subscription`
   - Event Type: Only "Device Telemetry" checked
   - Endpoint: Azure Function → IoTHub_EventGrid
   
2. Click **Create** button at the bottom

3. Wait 2-3 minutes for the subscription to provision
   - Status will show "Provisioning..." then "Succeeded"

---

## ✅ Verification

### Method 1: Azure Portal

1. Stay on the IoT Hub **Events** page
2. Click on **Event Subscriptions** tab
3. You should see: `iot-to-adt-subscription` with Status: **Active**

### Method 2: Azure CLI

```bash
cd /home/hs32/Documents/Projects/adt/azure-setup

./az-docker.sh eventgrid event-subscription list \
  --source-resource-id "/subscriptions/2128b63d-ecaf-42c5-bb3c-b9ba6919e10d/resourceGroups/DT_Research/providers/Microsoft.Devices/IotHubs/researchdt" \
  --query "[].{Name:name,Status:provisioningState}" -o table
```

Expected output:
```
Name                      Status
------------------------  ---------
iot-to-adt-subscription   Succeeded
```

### Method 3: Check Function App Logs

1. In Azure Portal, go to **adt-telemetry-router** Function App
2. Click **Log stream** in left menu
3. You should see messages like:
   ```
   [Information] Updating zone_A with temperature: 30.5
   [Information] Updated twin zone_A successfully
   ```

### Method 4: Query Digital Twins

```bash
cd /home/hs32/Documents/Projects/adt/azure-setup

# Run this command multiple times (wait 10 seconds between)
./az-docker.sh dt twin show -n farm-digital-twin --twin-id zone_A \
  --query "{temp:temperature,hum:humidity,soil:soilMoisture,updated:lastUpdated}"
```

Expected: `lastUpdated` timestamp should change with each query

---

## 🔍 Troubleshooting

### Issue: "Create" button is grayed out

**Solution**: Make sure all required fields are filled:
- Name is entered
- Event type is selected
- Endpoint is configured

### Issue: Endpoint validation fails

**Possible Causes**:
1. Function App is not running
2. Function doesn't exist
3. Network connectivity issue

**Solutions**:
1. Go to Function App → Functions → Verify `IoTHub_EventGrid` exists
2. Go to Function App → Overview → Verify status is "Running"
3. Wait 2-3 minutes and try again

### Issue: Subscription created but no data flowing

**Check**:
1. Node-RED is running:
   ```bash
   ps aux | grep node-red | grep -v grep
   ```
2. IoT Hub receiving messages:
   ```bash
   ./az-docker.sh iot hub monitor-events --hub-name researchdt --device-id pc_sim_01
   ```
3. Function App has proper role:
   ```bash
   PRINCIPAL_ID=$(./az-docker.sh functionapp identity show -n adt-telemetry-router -g adt-farm-rg --query principalId -o tsv)
   ./az-docker.sh role assignment list --assignee "$PRINCIPAL_ID" | grep "Azure Digital Twins Data Owner"
   ```

### Issue: Authentication errors in Function logs

**Solution**: Verify Managed Identity has correct role:
```bash
cd /home/hs32/Documents/Projects/adt/azure-setup

# Check role assignment
./az-docker.sh role assignment list \
  --scope "/subscriptions/2128b63d-ecaf-42c5-bb3c-b9ba6919e10d/resourceGroups/adt-farm-rg/providers/Microsoft.DigitalTwins/digitalTwinsInstances/farm-digital-twin" \
  --query "[?principalId=='25d77024-ff03-47fb-9f1c-29e1bcd073a4'].roleDefinitionName"
```

Expected: `["Azure Digital Twins Data Owner"]`

---

## 📊 Expected Results After Setup

### 1. Real-Time Data in Azure Digital Twins Explorer

1. Open: https://explorer.digitaltwins.azure.net
2. Select: **farm-digital-twin**
3. Click on **zone_A** twin
4. In Properties panel, you should see values updating every 5-10 seconds:
   - `temperature`: ~25-35°C (matches Dhaka weather)
   - `humidity`: ~60-85% (matches Dhaka weather)
   - `soilMoisture`: ~50-80% (calculated from weather)
   - `lastUpdated`: Current timestamp

### 2. Function Execution Count

In Azure Portal → Function App → Overview:
- **Function Execution Count**: Increasing every 5-10 seconds
- **Success Rate**: ~100%

### 3. IoT Hub Metrics

In Azure Portal → IoT Hub → Metrics:
- **Telemetry messages sent**: Increasing
- **Event Grid deliveries**: Matching telemetry message count

---

## 🎯 Success Criteria

✅ Event subscription status: **Active**  
✅ Function logs showing twin updates  
✅ Digital Twins `lastUpdated` timestamp changing  
✅ Values in Azure Digital Twins Explorer updating in real-time  

---

## 📚 Additional Resources

- **Azure Event Grid Documentation**: https://docs.microsoft.com/azure/event-grid/
- **IoT Hub Event Grid Integration**: https://docs.microsoft.com/azure/iot-hub/iot-hub-event-grid
- **Azure Functions Event Grid Trigger**: https://docs.microsoft.com/azure/azure-functions/functions-bindings-event-grid-trigger

---

## 💡 Why Manual Setup?

Azure CLI authentication issues prevented automated subscription creation:
- Error: "InvalidAuthenticationToken - claims 'puid' or 'altsecid' or 'oid' missing"
- Cross-resource-group subscriptions have additional validation requirements
- Azure Portal handles authentication and validation automatically

---

**Created**: December 17, 2025
**Purpose**: Complete Event Grid subscription for real-time data flow
**Time Required**: ~5 minutes
**Difficulty**: Easy (point-and-click)
