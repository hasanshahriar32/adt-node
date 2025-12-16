#!/bin/bash

# Deploy Azure Function for IoT Hub to Digital Twins routing

set -e

# Use Docker-based Azure CLI
AZ="./az-docker.sh"

# Configuration
RESOURCE_GROUP="adt-farm-rg"
FUNCTION_APP_NAME="adt-telemetry-router"
FUNCTION_DIR="../azure-functions"

echo "=========================================="
echo "Azure Function Deployment"
echo "=========================================="
echo ""

# Check if logged in
$AZ account show > /dev/null 2>&1 || {
    echo "❌ Not logged in to Azure CLI"
    echo "Please run: $AZ login"
    exit 1
}

# Check if function directory exists
if [ ! -d "$FUNCTION_DIR" ]; then
    echo "❌ Function directory not found: $FUNCTION_DIR"
    exit 1
fi

echo "📦 Preparing function app for deployment..."

# Create deployment package
cd $FUNCTION_DIR
echo "  → Installing dependencies..."
pip install -r requirements.txt --target .python_packages/lib/site-packages

echo "  → Creating deployment package..."
zip -r ../function-deploy.zip . -x "*.git*" -x "*__pycache__*" -x "*.pyc"
cd ..

echo ""
echo "🚀 Deploying to Azure Function App: $FUNCTION_APP_NAME"

$AZ functionapp deployment source config-zip \
    --resource-group $RESOURCE_GROUP \
    --name $FUNCTION_APP_NAME \
    --src function-deploy.zip \
    --output table

# Cleanup
rm function-deploy.zip
rm -rf $FUNCTION_DIR/.python_packages

echo ""
echo "=========================================="
echo "✅ Function Deployment Complete!"
echo "=========================================="
echo ""
echo "Testing endpoint:"
echo "curl -X POST https://${FUNCTION_APP_NAME}.azurewebsites.net/api/predict \\"
echo "  -H 'Content-Type: application/json' \\"
echo "  -d '{\"temperature\": 28.5, \"humidity\": 75.0, \"soilMoisture\": 65.0}'"
echo ""
echo "Monitor logs:"
echo "$AZ functionapp log tail --name $FUNCTION_APP_NAME --resource-group $RESOURCE_GROUP"
echo ""
