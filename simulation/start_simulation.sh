#!/bin/bash
# Load environment variables from .env
if [ -f .env ]; then
  echo "Loading environment variables from .env..."
  # Remove Windows line endings if present
  sed -i 's/\r$//' .env
  set -a
  source .env
  set +a
fi

# Determine SAS Token
if [ -n "$IOT_HUB_SAS_KEY" ] && [ -n "$IOT_HUB_HOSTNAME" ] && [ -n "$DEVICE_ID" ]; then
  echo "Generating SAS Token from Primary Key..."
  SAS_TOKEN=$(python3 generate_sas.py "$IOT_HUB_HOSTNAME" "$DEVICE_ID" "$IOT_HUB_SAS_KEY")
  echo "SAS Token generated."
elif [ -n "$IOT_HUB_SAS_TOKEN" ]; then
  echo "Using provided SAS Token..."
  SAS_TOKEN="$IOT_HUB_SAS_TOKEN"
else
  echo "WARNING: No SAS Key or Token provided. Simulation might fail to connect."
  SAS_TOKEN=""
fi

# Always inject variables
echo "Injecting configuration into flows..."
python3 -c "import sys; 
content = sys.stdin.read(); 
content = content.replace('\$(IOT_HUB_SAS_TOKEN)', '$SAS_TOKEN'); 
content = content.replace('\$(IOT_HUB_HOSTNAME)', '$IOT_HUB_HOSTNAME'); 
content = content.replace('\$(DEVICE_ID)', '$DEVICE_ID'); 
print(content)" < flows.json > flows_runtime.json

# Create credentials file explicitly
cat <<EOF > flows_runtime_cred.json
{
    "mqtt_broker_config": {
        "user": "$IOT_HUB_HOSTNAME/$DEVICE_ID/?api-version=2021-04-12",
        "password": "$SAS_TOKEN"
    }
}
EOF

FLOW_FILE="flows_runtime.json"

# Start Node-RED with the runtime flow file
echo "Starting Node-RED Simulation with $FLOW_FILE..."
echo "Open your browser at http://localhost:1880"
./node_modules/.bin/node-red -u . $FLOW_FILE
