#!/bin/bash

# Create Event Grid subscription to route IoT Hub telemetry to Azure Function

set -e

# Use Docker-based Azure CLI
AZ="./az-docker.sh"

# Configuration
RESOURCE_GROUP="adt-farm-rg"
IOT_HUB_NAME="researchdt"
FUNCTION_APP_NAME="adt-telemetry-router"

echo "=========================================="
echo "Event Grid Subscription Setup"
echo "=========================================="
echo ""

# Check if logged in
$AZ account show > /dev/null 2>&1 || {
    echo "❌ Not logged in to Azure CLI"
    echo "Please run: $AZ login"
    exit 1
}

# Get IoT Hub resource ID
echo "Getting IoT Hub resource ID..."
IOT_HUB_ID=$($AZ iot hub show --name $IOT_HUB_NAME --query id -o tsv)

# Get Function App event grid key
echo "Getting Function App webhook endpoint..."
FUNCTION_KEY=$($AZ functionapp keys list \
    --name $FUNCTION_APP_NAME \
    --resource-group $RESOURCE_GROUP \
    --query systemKeys.eventgrid_extension -o tsv 2>/dev/null || echo "")

if [ -z "$FUNCTION_KEY" ]; then
    echo "⚠️  Event Grid extension key not found. Generating..."
    # Trigger key creation by restarting function app
    $AZ functionapp restart --name $FUNCTION_APP_NAME --resource-group $RESOURCE_GROUP
    sleep 10
    FUNCTION_KEY=$($AZ functionapp keys list \
        --name $FUNCTION_APP_NAME \
        --resource-group $RESOURCE_GROUP \
        --query systemKeys.eventgrid_extension -o tsv)
fi

WEBHOOK_URL="https://${FUNCTION_APP_NAME}.azurewebsites.net/runtime/webhooks/eventgrid?functionName=IoTHub_EventGrid&code=$FUNCTION_KEY"

echo "✅ Webhook URL: $WEBHOOK_URL"
echo ""

# Create Event Grid subscription
echo "Creating Event Grid subscription..."
$AZ eventgrid event-subscription create \
    --name iot-to-adt-subscription \
    --source-resource-id "$IOT_HUB_ID" \
    --endpoint-type webhook \
    --endpoint "$WEBHOOK_URL" \
    --included-event-types Microsoft.Devices.DeviceTelemetry \
    --output table

echo ""
echo "=========================================="
echo "✅ Event Grid Subscription Created!"
echo "=========================================="
echo ""
echo "IoT Hub telemetry will now flow to Digital Twins via Azure Function"
echo ""
echo "Verify setup:"
echo "  $AZ eventgrid event-subscription list --source-resource-id $IOT_HUB_ID --output table"
echo ""
