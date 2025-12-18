#!/bin/bash

# Deploy Azure Function
echo "Creating deployment package..."
cd "$(dirname "$0")"
zip -q -r function-app.zip . -x "*.pyc" -x "__pycache__/*" -x "*.sh" -x "*.md"

echo "Deploying to Azure..."
# Try to use az from different possible locations
if command -v az &> /dev/null; then
    az functionapp deployment source config-zip \
        --resource-group adt-farm-rg \
        --name adt-telemetry-router \
        --src function-app.zip \
        --build-remote true \
        --timeout 600
elif [ -f "/usr/bin/az" ]; then
    /usr/bin/az functionapp deployment source config-zip \
        --resource-group adt-farm-rg \
        --name adt-telemetry-router \
        --src function-app.zip \
        --build-remote true \
        --timeout 600
elif python3 -m azure.cli &> /dev/null; then
    python3 -m azure.cli functionapp deployment source config-zip \
        --resource-group adt-farm-rg \
        --name adt-telemetry-router \
        --src function-app.zip \
        --build-remote true \
        --timeout 600
else
    echo "ERROR: Azure CLI not found!"
    echo "Please install it with: curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash"
    echo ""
    echo "Or deploy manually via Azure Portal:"
    echo "1. Go to https://portal.azure.com"
    echo "2. Find your function app: adt-telemetry-router"
    echo "3. Go to Deployment Center > Manual Deployment"
    echo "4. Upload function-app.zip"
    rm function-app.zip
    exit 1
fi

echo "Cleaning up..."
rm function-app.zip

echo "Deployment complete!"
