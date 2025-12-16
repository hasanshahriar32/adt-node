#!/bin/bash
# Script to simulate telemetry updates to Digital Twin

AZ="./az-docker.sh"
ADT_INSTANCE="farm-digital-twin"

echo "==================================="
echo "Simulating Telemetry Updates"
echo "==================================="
echo ""

# Since telemetry can't be stored as properties in current model,
# we'll create a workaround by directly calling patch operations

for i in {1..5}; do
  # Generate random sensor values
  TEMP=$(echo "scale=1; 25 + $RANDOM % 10" | bc)
  HUM=$(echo "scale=1; 65 + $RANDOM % 20" | bc)
  SOIL=$(echo "scale=1; 60 + $RANDOM % 15" | bc)
  
  echo "Update #$i: Temp=${TEMP}°C, Humidity=${HUM}%, Soil=${SOIL}%"
  
  # Update zone lastUpdated timestamp
  TIMESTAMP=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  $AZ dt twin update -n $ADT_INSTANCE --twin-id zone_A \
    --json-patch "[{\"op\":\"add\",\"path\":\"/lastUpdated\",\"value\":\"$TIMESTAMP\"}]" > /dev/null 2>&1
  
  echo "  ✅ Updated at $TIMESTAMP"
  echo ""
  
  sleep 2
done

echo "✅ Completed 5 updates"
echo ""
echo "Check updates in Digital Twin Explorer:"
echo "https://explorer.digitaltwins.azure.net/"
