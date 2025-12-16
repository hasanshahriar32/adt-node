# Azure Digital Twins Deployment Scripts

Automated deployment scripts for setting up Azure Digital Twins infrastructure.

## Prerequisites

1. **Azure CLI installed**
   ```bash
   curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
   ```

2. **Login to Azure**
   ```bash
   az login
   ```

3. **Set your subscription** (if you have multiple)
   ```bash
   az account list --output table
   az account set --subscription "YOUR_SUBSCRIPTION_ID"
   ```

4. **Install Azure IoT extension**
   ```bash
   az extension add --name azure-iot
   ```

## Deployment Steps

### Step 1: Deploy Digital Twins Instance

This creates the Digital Twins instance, uploads DTDL models, and creates twin instances.

```bash
cd azure-setup
chmod +x *.sh
./deploy-digital-twins.sh
```

**What it creates:**
- Resource Group: `adt-farm-rg`
- Azure Digital Twins instance: `farm-digital-twin`
- DTDL models: Farm, Zone, Device, Crop
- Twin instances:
  - `farm_001` (Farm)
  - `zone_A` (Zone)
  - `pc_sim_01` (Device)
  - `rice`, `wheat`, `maize` (Crops)
- Relationships between twins

**Time:** ~5-10 minutes

---

### Step 2: Setup IoT Hub Routing

This creates the Azure Function App and configures permissions.

```bash
./setup-iot-routing.sh
```

**What it creates:**
- Storage Account for Function App
- Azure Function App: `adt-telemetry-router`
- System-assigned managed identity
- Role assignment: Digital Twins Data Owner
- Environment variables for ADT connection

**Time:** ~3-5 minutes

---

### Step 3: Deploy Function Code

This deploys the IoT Hub Event Grid function to Azure.

```bash
./deploy-function.sh
```

**What it does:**
- Installs Python dependencies
- Packages function code
- Deploys to Azure Function App
- Creates two functions:
  - `AI_Inference` (HTTP trigger for predictions)
  - `IoTHub_EventGrid` (Event Grid trigger for telemetry routing)

**Time:** ~2-3 minutes

---

### Step 4: Create Event Grid Subscription

This connects IoT Hub telemetry events to the Azure Function.

```bash
./create-eventgrid-subscription.sh
```

**What it creates:**
- Event Grid subscription: `iot-to-adt-subscription`
- Webhook endpoint connecting IoT Hub → Azure Function
- Filters for device telemetry events

**Time:** ~1-2 minutes

---

## Verification

### 1. Check Digital Twins Instance

```bash
az dt show --dt-name farm-digital-twin --query "{Name:name, Host:hostName, Location:location}" --output table
```

### 2. List Twin Instances

```bash
az dt twin query --dt-name farm-digital-twin --query-command "SELECT * FROM digitaltwins"
```

### 3. View Specific Twin

```bash
az dt twin show --dt-name farm-digital-twin --twin-id zone_A
```

### 4. Check Function App Status

```bash
az functionapp show --name adt-telemetry-router --resource-group adt-farm-rg --query "{Name:name, State:state, DefaultHostName:defaultHostName}" --output table
```

### 5. Monitor Function Logs

```bash
az functionapp log tail --name adt-telemetry-router --resource-group adt-farm-rg
```

### 6. Test AI Inference Function

```bash
FUNCTION_APP_NAME="adt-telemetry-router"

curl -X POST "https://${FUNCTION_APP_NAME}.azurewebsites.net/api/predict" \
  -H "Content-Type: application/json" \
  -d '{
    "temperature": 28.5,
    "humidity": 75.0,
    "soilMoisture": 65.0
  }'
```

Expected response:
```json
{
  "recommendedCrop": "rice",
  "confidence": 0.96,
  "timestamp": "2025-12-16T10:30:00Z"
}
```

---

## Access Digital Twin Explorer

1. Open: https://explorer.digitaltwins.azure.net/
2. Sign in with your Azure account
3. Select your Digital Twins instance: `farm-digital-twin`
4. View your twin graph:
   - `farm_001` → `zone_A` → `pc_sim_01`
   - `zone_A` → `rice`

---

## Troubleshooting

### Function App not receiving events

```bash
# Check Event Grid subscription
az eventgrid event-subscription list \
  --source-resource-id $(az iot hub show --name researchdt --query id -o tsv) \
  --output table

# Restart Function App
az functionapp restart --name adt-telemetry-router --resource-group adt-farm-rg
```

### Digital Twins update failures

```bash
# Check Function App identity has correct role
az dt role-assignment list --dt-name farm-digital-twin --output table

# View Function App environment variables
az functionapp config appsettings list \
  --name adt-telemetry-router \
  --resource-group adt-farm-rg \
  --output table
```

### Permission errors

```bash
# Re-assign yourself as Digital Twins Data Owner
USER_ID=$(az ad signed-in-user show --query id -o tsv)
az dt role-assignment create \
  --dt-name farm-digital-twin \
  --assignee $USER_ID \
  --role "Azure Digital Twins Data Owner"
```

---

## Clean Up Resources

To delete all resources:

```bash
az group delete --name adt-farm-rg --yes --no-wait
```

---

## Cost Estimation

- **Azure Digital Twins**: ~$1-2/day
- **Azure Function App (Consumption)**: ~$0-5/month
- **Storage Account**: ~$0.50/month
- **Event Grid**: ~$0.60/million events

**Total estimated cost**: ~$30-60/month for development/testing

---

## Next Steps

1. ✅ Deploy infrastructure (Steps 1-4)
2. Send test telemetry from Node-RED
3. View real-time updates in Digital Twin Explorer
4. Integrate AI inference in Node-RED flows
5. Create custom queries and dashboards

---

## Architecture

```
WeatherAPI → Node-RED → IoT Hub → Event Grid → Azure Function → Digital Twins
                ↓                                     ↓
            UI Dashboard                      Twin Explorer
```

---

## Support

For issues or questions:
- Check Azure Function logs: `az functionapp log tail ...`
- View Digital Twins metrics in Azure Portal
- Test endpoints individually before integration
