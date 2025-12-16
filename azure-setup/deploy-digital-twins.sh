#!/bin/bash

# Azure Digital Twins Deployment Script
# This script creates and configures Azure Digital Twins instance

set -e  # Exit on error

# Get script directory and use Docker-based Azure CLI
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
AZ="$SCRIPT_DIR/az-docker.sh"

# Configuration
RESOURCE_GROUP="adt-farm-rg"
LOCATION="southeastasia"
ADT_INSTANCE_NAME="farm-digital-twin"
IOT_HUB_NAME="researchdt"
FUNCTION_APP_NAME="adt-telemetry-router"
STORAGE_ACCOUNT_NAME="adtfuncstorage$(date +%s | tail -c 6)"

echo "=========================================="
echo "Azure Digital Twins Setup"
echo "=========================================="
echo ""

# Check if logged in
echo "Checking Azure CLI login status..."
if ! $AZ account show --output none 2>/dev/null; then
    echo "❌ Not logged in to Azure CLI"
    echo "Please run: ./az-docker.sh login"
    exit 1
fi

echo "✅ Logged in as: $($AZ account show --query user.name -o tsv)"
echo "📍 Subscription: $($AZ account show --query name -o tsv)"
echo ""

# Check if Resource Group exists
# Create or use existing resource group
echo "Creating resource group: $RESOURCE_GROUP in $LOCATION"
$AZ group create \
    --name $RESOURCE_GROUP \
    --location $LOCATION \
    --output table

echo ""

# Create Azure Digital Twins instance
echo "Creating Azure Digital Twins instance: $ADT_INSTANCE_NAME in $LOCATION"
$AZ dt create \
    -g $RESOURCE_GROUP \
    -n $ADT_INSTANCE_NAME \
    -l $LOCATION \
    --mi-system-assigned \
    --output table

echo ""

# Assign yourself as owner (for Digital Twin Explorer access)
echo "Assigning Digital Twins Data Owner role to current user..."
USER_ID=$($AZ ad signed-in-user show --query id -o tsv | tr -d '\r\n')
ADT_ID=$($AZ dt show -n $ADT_INSTANCE_NAME -g $RESOURCE_GROUP --query id -o tsv | tr -d '\r\n')
$AZ role assignment create \
    --assignee "$USER_ID" \
    --role "Azure Digital Twins Data Owner" \
    --scope "$ADT_ID" \
    --output table 2>/dev/null || echo "⚠️  Role assignment failed (may need admin consent), but continuing..."

echo ""

# Upload DTDL models
echo "Uploading DTDL models to Azure Digital Twins..."
MODELS_DIR="../digital-twins/models"

echo "  → Uploading Farm model..."
$AZ dt model create \
    -n $ADT_INSTANCE_NAME \
    --models "$MODELS_DIR/Farm.json" \
    --output table

echo "  → Uploading Crop model..."
$AZ dt model create \
    -n $ADT_INSTANCE_NAME \
    --models "$MODELS_DIR/Crop.json" \
    --output table

echo "  → Uploading Zone model..."
$AZ dt model create \
    -n $ADT_INSTANCE_NAME \
    --models "$MODELS_DIR/Zone.json" \
    --output table

echo "  → Uploading Device model..."
$AZ dt model create \
    -n $ADT_INSTANCE_NAME \
    --models "$MODELS_DIR/Device.json" \
    --output table

echo ""

# Create twin instances
echo "Creating digital twin instances..."

# Create Farm twin
echo "  → Creating Farm twin: farm_001"
$AZ dt twin create \
    -n $ADT_INSTANCE_NAME \
    --dtmi "dtmi:agriculture:Farm;1" \
    --twin-id "farm_001" \
    --properties '{
        "name": "Research Farm",
        "location": "Dhaka, Bangladesh",
        "totalArea": 10.5,
        "owner": "Agricultural Research Institute"
    }' \
    --output table

# Create Crop twins
echo "  → Creating Crop twin: rice"
$AZ dt twin create \
    -n $ADT_INSTANCE_NAME \
    --dtmi "dtmi:agriculture:Crop;1" \
    --twin-id "rice" \
    --properties '{
        "name": "Rice",
        "scientificName": "Oryza sativa",
        "optimalTemperatureMin": 20.0,
        "optimalTemperatureMax": 35.0,
        "optimalHumidityMin": 60.0,
        "optimalHumidityMax": 80.0,
        "optimalSoilMoistureMin": 70.0,
        "optimalSoilMoistureMax": 90.0,
        "growthDuration": 120,
        "season": "Monsoon"
    }' \
    --output table

echo "  → Creating Crop twin: wheat"
$AZ dt twin create \
    -n $ADT_INSTANCE_NAME \
    --dtmi "dtmi:agriculture:Crop;1" \
    --twin-id "wheat" \
    --properties '{
        "name": "Wheat",
        "scientificName": "Triticum aestivum",
        "optimalTemperatureMin": 12.0,
        "optimalTemperatureMax": 25.0,
        "optimalHumidityMin": 40.0,
        "optimalHumidityMax": 70.0,
        "optimalSoilMoistureMin": 50.0,
        "optimalSoilMoistureMax": 75.0,
        "growthDuration": 150,
        "season": "Winter"
    }' \
    --output table

echo "  → Creating Crop twin: maize"
$AZ dt twin create \
    -n $ADT_INSTANCE_NAME \
    --dtmi "dtmi:agriculture:Crop;1" \
    --twin-id "maize" \
    --properties '{
        "name": "Maize",
        "scientificName": "Zea mays",
        "optimalTemperatureMin": 18.0,
        "optimalTemperatureMax": 32.0,
        "optimalHumidityMin": 50.0,
        "optimalHumidityMax": 75.0,
        "optimalSoilMoistureMin": 55.0,
        "optimalSoilMoistureMax": 80.0,
        "growthDuration": 100,
        "season": "Summer"
    }' \
    --output table

# Create Zone twin
echo "  → Creating Zone twin: zone_A"
$AZ dt twin create \
    -n $ADT_INSTANCE_NAME \
    --dtmi "dtmi:agriculture:Zone;1" \
    --twin-id "zone_A" \
    --properties '{
        "name": "Zone A",
        "area": 2.5,
        "soilType": "Clay Loam",
        "currentCrop": "rice",
        "recommendedCrop": "rice",
        "recommendationConfidence": 0.96
    }' \
    --output table

# Create Device twin
echo "  → Creating Device twin: pc_sim_01"
$AZ dt twin create \
    -n $ADT_INSTANCE_NAME \
    --dtmi "dtmi:agriculture:Device;1" \
    --twin-id "pc_sim_01" \
    --properties '{
        "deviceId": "pc_sim_01",
        "deviceType": "Environment Sensor",
        "firmwareVersion": "1.0.0",
        "status": "active"
    }' \
    --output table

echo ""

# Create relationships
echo "Creating relationships between twins..."

echo "  → farm_001 hasZone zone_A"
$AZ dt twin relationship create \
    -n $ADT_INSTANCE_NAME \
    --relationship-id "farm_001_has_zone_A" \
    --relationship "hasZone" \
    --twin-id "farm_001" \
    --target "zone_A" \
    --output table

echo "  → zone_A hasDevice pc_sim_01"
$AZ dt twin relationship create \
    -n $ADT_INSTANCE_NAME \
    --relationship-id "zone_A_has_device_pc_sim_01" \
    --relationship "hasDevice" \
    --twin-id "zone_A" \
    --target "pc_sim_01" \
    --output table

echo "  → zone_A growsCrop rice"
$AZ dt twin relationship create \
    -n $ADT_INSTANCE_NAME \
    --relationship-id "zone_A_grows_rice" \
    --relationship "growsCrop" \
    --twin-id "zone_A" \
    --target "rice" \
    --output table

echo ""

# Get ADT endpoint
ADT_ENDPOINT=$($AZ dt show -n $ADT_INSTANCE_NAME --query hostName -o tsv)
echo "=========================================="
echo "✅ Azure Digital Twins Setup Complete!"
echo "=========================================="
echo ""
echo "📍 Instance Name: $ADT_INSTANCE_NAME"
echo "🔗 Endpoint: https://$ADT_ENDPOINT"
echo "🌐 Explorer URL: https://explorer.digitaltwins.azure.net/"
echo ""
echo "Created Digital Twins:"
echo "  • farm_001 (Farm)"
echo "  • zone_A (Zone)"
echo "  • pc_sim_01 (Device)"
echo "  • rice, wheat, maize (Crops)"
echo ""
echo "Next steps:"
echo "  1. Run: ./setup-iot-routing.sh"
echo "  2. Open Digital Twin Explorer and connect to: $ADT_INSTANCE_NAME"
echo "  3. Deploy Azure Function: ./deploy-function.sh"
echo ""
