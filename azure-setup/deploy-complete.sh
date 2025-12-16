#!/bin/bash

# Complete Azure Digital Twins Deployment
# Simplified version that creates everything in one go

set -e

cd "$(dirname "$0")"
AZ="./az-docker.sh"

# Configuration
RESOURCE_GROUP="adt-farm-rg"
LOCATION="southeastasia"
ADT_INSTANCE_NAME="farm-digital-twin"
MODELS_DIR="../digital-twins/models"

echo "=========================================="
echo "Azure Digital Twins Complete Deployment"
echo "=========================================="
echo ""

# Login check
echo "Checking login..."
if ! $AZ account show --output none 2>/dev/null; then
    echo "❌ Not logged in. Run: ./az-docker.sh login"
    exit 1
fi

echo "✅ Logged in as: $($AZ account show --query user.name -o tsv | tr -d '\r\n')"
echo ""

# Create resource group
echo "📦 Creating resource group..."
$AZ group create --name $RESOURCE_GROUP --location $LOCATION --output none 2>/dev/null || echo "Resource group exists"

# Create Digital Twins instance
echo "🏗️  Creating Azure Digital Twins instance..."
$AZ dt create -g $RESOURCE_GROUP -n $ADT_INSTANCE_NAME -l $LOCATION --mi-system-assigned --output none

echo "✅ Azure Digital Twins instance created!"
echo ""

# Assign role with clean IDs
echo "🔐 Assigning permissions..."
sleep 5  # Wait for instance to fully initialize

USER_ID=$($AZ ad signed-in-user show --query id -o tsv | tr -d '\r\n' | sed 's/\x1b\[[0-9;]*[a-zA-Z]//g')
ADT_ID=$($AZ dt show -n $ADT_INSTANCE_NAME -g $RESOURCE_GROUP --query id -o tsv | tr -d '\r\n' | sed 's/\x1b\[[0-9;]*[a-zA-Z]//g')

$AZ role assignment create \
    --assignee "$USER_ID" \
    --role "Azure Digital Twins Data Owner" \
    --scope "$ADT_ID" \
    --output none

echo "✅ Permissions assigned!"
echo "⏳ Waiting 20 seconds for role propagation..."
sleep 20
echo ""

# Upload models
echo "📤 Uploading DTDL models..."
$AZ dt model create -n $ADT_INSTANCE_NAME --models "$MODELS_DIR/Farm.json" --output none
echo "  ✓ Farm"

$AZ dt model create -n $ADT_INSTANCE_NAME --models "$MODELS_DIR/Crop.json" --output none
echo "  ✓ Crop"

$AZ dt model create -n $ADT_INSTANCE_NAME --models "$MODELS_DIR/Zone.json" --output none
echo "  ✓ Zone"

$AZ dt model create -n $ADT_INSTANCE_NAME --models "$MODELS_DIR/Device.json" --output none
echo "  ✓ Device"

echo ""
echo "📊 Creating digital twins..."

# Create Farm twin
$AZ dt twin create -n $ADT_INSTANCE_NAME --dtmi "dtmi:agriculture:Farm;1" --twin-id "farm_001" \
  --properties '{"name":"Research Farm","location":"Dhaka, Bangladesh","totalArea":10.5,"owner":"Agricultural Research Institute"}' \
  --output none
echo "  ✓ farm_001 (Farm)"

# Create Crop twins
$AZ dt twin create -n $ADT_INSTANCE_NAME --dtmi "dtmi:agriculture:Crop;1" --twin-id "rice" \
  --properties '{"name":"Rice","scientificName":"Oryza sativa","optimalTemperatureMin":20.0,"optimalTemperatureMax":35.0,"optimalHumidityMin":60.0,"optimalHumidityMax":80.0,"optimalSoilMoistureMin":70.0,"optimalSoilMoistureMax":90.0,"growthDuration":120,"season":"Monsoon"}' \
  --output none
echo "  ✓ rice (Crop)"

$AZ dt twin create -n $ADT_INSTANCE_NAME --dtmi "dtmi:agriculture:Crop;1" --twin-id "wheat" \
  --properties '{"name":"Wheat","scientificName":"Triticum aestivum","optimalTemperatureMin":12.0,"optimalTemperatureMax":25.0,"optimalHumidityMin":40.0,"optimalHumidityMax":70.0,"optimalSoilMoistureMin":50.0,"optimalSoilMoistureMax":75.0,"growthDuration":150,"season":"Winter"}' \
  --output none
echo "  ✓ wheat (Crop)"

$AZ dt twin create -n $ADT_INSTANCE_NAME --dtmi "dtmi:agriculture:Crop;1" --twin-id "maize" \
  --properties '{"name":"Maize","scientificName":"Zea mays","optimalTemperatureMin":18.0,"optimalTemperatureMax":32.0,"optimalHumidityMin":50.0,"optimalHumidityMax":75.0,"optimalSoilMoistureMin":55.0,"optimalSoilMoistureMax":80.0,"growthDuration":100,"season":"Summer"}' \
  --output none
echo "  ✓ maize (Crop)"

# Create Zone twin
$AZ dt twin create -n $ADT_INSTANCE_NAME --dtmi "dtmi:agriculture:Zone;1" --twin-id "zone_A" \
  --properties '{"name":"Zone A","area":2.5,"soilType":"Clay Loam","currentCrop":"rice","recommendedCrop":"rice","recommendationConfidence":0.96}' \
  --output none
echo "  ✓ zone_A (Zone)"

# Create Device twin
$AZ dt twin create -n $ADT_INSTANCE_NAME --dtmi "dtmi:agriculture:Device;1" --twin-id "pc_sim_01" \
  --properties '{"deviceId":"pc_sim_01","deviceType":"Environment Sensor","firmwareVersion":"1.0.0","status":"active"}' \
  --output none
echo "  ✓ pc_sim_01 (Device)"

echo ""
echo "🔗 Creating relationships..."

# Create relationships
$AZ dt twin relationship create -n $ADT_INSTANCE_NAME \
  --relationship-id "farm_001_has_zone_A" --relationship "hasZone" \
  --twin-id "farm_001" --target "zone_A" --output none
echo "  ✓ farm_001 → zone_A"

$AZ dt twin relationship create -n $ADT_INSTANCE_NAME \
  --relationship-id "zone_A_has_device_pc_sim_01" --relationship "hasDevice" \
  --twin-id "zone_A" --target "pc_sim_01" --output none
echo "  ✓ zone_A → pc_sim_01"

$AZ dt twin relationship create -n $ADT_INSTANCE_NAME \
  --relationship-id "zone_A_grows_rice" --relationship "growsCrop" \
  --twin-id "zone_A" --target "rice" --output none
echo "  ✓ zone_A → rice"

# Get endpoint
ADT_ENDPOINT=$($AZ dt show -n $ADT_INSTANCE_NAME --query hostName -o tsv | tr -d '\r\n')

echo ""
echo "=========================================="
echo "✅ Deployment Complete!"
echo "=========================================="
echo ""
echo "📍 Instance: $ADT_INSTANCE_NAME"
echo "🌐 Endpoint: https://$ADT_ENDPOINT"
echo "🔍 Explorer: https://explorer.digitaltwins.azure.net/"
echo ""
echo "Digital Twins Created:"
echo "  • farm_001 (Farm)"
echo "  • zone_A (Zone)"
echo "  • pc_sim_01 (Device)"
echo "  • rice, wheat, maize (Crops)"
echo ""
echo "Next steps:"
echo "  1. Open Digital Twin Explorer: https://explorer.digitaltwins.azure.net/"
echo "  2. Connect to instance: $ADT_INSTANCE_NAME"
echo "  3. Run: ./setup-iot-routing.sh (to connect IoT Hub)"
echo ""
