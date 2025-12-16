#!/bin/bash

# IoT Hub to Azure Digital Twins Routing Setup
# Creates Event Grid subscription to route telemetry to Azure Function

set -e

# Use Docker-based Azure CLI
AZ="./az-docker.sh"

# Configuration
RESOURCE_GROUP="adt-farm-rg"
LOCATION="southeastasia"
IOT_HUB_NAME="researchdt"
ADT_INSTANCE_NAME="farm-digital-twin"
FUNCTION_APP_NAME="adt-telemetry-router"
STORAGE_ACCOUNT_NAME="adtfuncstorage$(date +%s | tail -c 6)"

echo "=========================================="
echo "IoT Hub to Digital Twins Routing Setup"
echo "=========================================="
echo ""

# Check if logged in
$AZ account show > /dev/null 2>&1 || {
    echo "❌ Not logged in to Azure CLI"
    echo "Please run: $AZ login"
    exit 1
}

# Get IoT Hub resource ID
echo "Getting IoT Hub information..."
IOT_HUB_ID=$($AZ iot hub show --name $IOT_HUB_NAME --query id -o tsv)
echo "✅ Found IoT Hub: $IOT_HUB_NAME"
echo ""

# Create Storage Account for Azure Function
echo "Creating storage account: $STORAGE_ACCOUNT_NAME"
az storage account create \
    --name $STORAGE_ACCOUNT_NAME \
    --resource-group $RESOURCE_GROUP \
    --location $LOCATION \
    --sku Standard_LRS \
    --output table

echo ""

# Create Function App
echo "Creating Azure Function App: $FUNCTION_APP_NAME"
$AZ functionapp create \
    --resource-group $RESOURCE_GROUP \
    --name $FUNCTION_APP_NAME \
    --storage-account $STORAGE_ACCOUNT_NAME \
    --consumption-plan-location $LOCATION \
    --runtime python \
    --runtime-version 3.11 \
    --functions-version 4 \
    --os-type Linux \
    --assign-identity [system] \
    --output table

echo ""

# Get Function App identity
echo "Getting Function App managed identity..."
FUNCTION_IDENTITY=$($AZ functionapp identity show \
    --name $FUNCTION_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query principalId -o tsv)

echo "✅ Function App Identity: $FUNCTION_IDENTITY"
echo ""

# Assign Digital Twins Data Owner role to Function App
echo "Granting Function App access to Digital Twins..."
$AZ dt role-assignment create \
    --resource-group $RESOURCE_GROUP \
    --dts-name $ADT_INSTANCE_NAME \
    --assignee $FUNCTION_IDENTITY \
    --role "Azure Digital Twins Data Owner" \
    --output table

echo ""

# Configure Function App settings
echo "Configuring Function App environment variables..."
ADT_ENDPOINT=$($AZ dt show --dt-name $ADT_INSTANCE_NAME --query hostName -o tsv)

$AZ functionapp config appsettings set \
    --name $FUNCTION_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --settings \
        "ADT_INSTANCE_URL=https://$ADT_ENDPOINT" \
        "DEVICE_TWIN_ID=pc_sim_01" \
        "ZONE_TWIN_ID=zone_A" \
    --output table

echo ""

# Get Function App endpoint for Event Grid
FUNCTION_KEY=$($AZ functionapp keys list \
    --name $FUNCTION_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query systemKeys.eventgrid_extension -o tsv)

WEBHOOK_URL="https://${FUNCTION_APP_NAME}.azurewebsites.net/runtime/webhooks/eventgrid?functionName=IoTHub_EventGrid&code=$FUNCTION_KEY"

echo ""
echo "=========================================="
echo "⚠️  Manual Step Required"
echo "=========================================="
echo ""
echo "Azure Function webhook endpoint:"
echo "$WEBHOOK_URL"
echo ""
echo "After deploying your Azure Function code, run:"
echo ""
echo "$AZ eventgrid event-subscription create \\"
echo "    --name iot-to-adt-subscription \\"
echo "    --source-resource-id $IOT_HUB_ID \\"
echo "    --endpoint-type webhook \\"
echo "    --endpoint $WEBHOOK_URL \\"
echo "    --included-event-types Microsoft.Devices.DeviceTelemetry"
echo ""
echo "=========================================="
echo "✅ Function App Setup Complete!"
echo "=========================================="
echo ""
echo "📍 Function App: $FUNCTION_APP_NAME"
echo "🔗 ADT Endpoint: https://$ADT_ENDPOINT"
echo ""
echo "Next step:"
echo "  Deploy function code: ./deploy-function.sh"
echo ""
