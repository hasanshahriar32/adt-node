#!/bin/bash
# Manually update digital twin with test telemetry

AZ="./az-docker.sh"

echo "Updating zone_A twin with test telemetry..."

$AZ dt twin update \
  -n farm-digital-twin \
  --twin-id zone_A \
  --json-patch '[
    {"op":"add","path":"/temperature","value":28.5},
    {"op":"add","path":"/humidity","value":72.0},
    {"op":"add","path":"/soilMoisture","value":65.0}
  ]'

echo ""
echo "✅ Twin updated with test data"
echo ""
echo "Query to verify:"
echo "./az-docker.sh dt twin query -n farm-digital-twin --query-command \"SELECT * FROM digitaltwins WHERE \\\$dtId = 'zone_A'\""
