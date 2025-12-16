# Azure Digital Twins Deployment Session - December 16, 2025

## Session Overview
This document records all steps taken to deploy Azure Digital Twins infrastructure after completing Phase 3 (IoT Hub connection). The goal was to enable Digital Twin Explorer visualization and set up the complete Azure infrastructure.

---

## Phase 4-5: Azure Digital Twins Infrastructure Setup

### Step 1: Created DTDL Models (Digital Twin Definition Language)

Created four DTDL v2 models to represent the farm infrastructure:

**1. Farm Model** (`digital-twins/models/Farm.json`)
- DTMI: `dtmi:agriculture:Farm;1`
- Properties: name, location, totalArea, owner
- Relationship: hasZone → Zone

**2. Zone Model** (`digital-twins/models/Zone.json`)
- DTMI: `dtmi:agriculture:Zone;1`
- Properties: name, area, soilType, currentCrop, recommendedCrop, recommendationConfidence, lastUpdated
- Telemetry: temperature, humidity, soilMoisture
- Relationships: hasDevice → Device, growsCrop → Crop

**3. Device Model** (`digital-twins/models/Device.json`)
- DTMI: `dtmi:agriculture:Device;1`
- Properties: deviceId, deviceType, firmwareVersion, status, lastSeen
- Telemetry: temperature, humidity, soilMoisture, batteryLevel

**4. Crop Model** (`digital-twins/models/Crop.json`)
- DTMI: `dtmi:agriculture:Crop;1`
- Properties: name, scientificName, optimal environmental ranges (temperature, humidity, soil moisture), growthDuration, season

---

### Step 2: Azure CLI Installation on Arch Linux

**Challenge**: Azure CLI was not installed on the system.

**Attempted Methods**:
1. **AUR Package Manager (yay)**:
   ```bash
   yay -S azure-cli --noconfirm
   ```
   - ❌ Failed: Mirror timeout issues

2. **pipx Installation**:
   ```bash
   sudo pacman -S --noconfirm python-pipx
   pipx install azure-cli --verbose
   ```
   - ❌ Failed: Installation took too long, dependencies issues

3. **Microsoft's Official Script**:
   ```bash
   curl -sL https://aka.ms/InstallAzureCLIDeb | sudo bash
   ```
   - ❌ Failed: Requires apt-get (Debian-based), not compatible with Arch

**✅ Solution: Docker-based Azure CLI**

Created a Docker wrapper script: `azure-setup/az-docker.sh`

```bash
#!/bin/bash
# Azure CLI Docker wrapper

# Create .azure directory if it doesn't exist
mkdir -p "$HOME/.azure"

docker run -it --rm \
  -v "$HOME/.azure:/root/.azure:rw" \
  -v "$(pwd)/..:/work:rw" \
  -w /work/azure-setup \
  mcr.microsoft.com/azure-cli:latest \
  az "$@"
```

**Setup Commands**:
```bash
# Start Docker daemon
sudo systemctl start docker
sudo systemctl enable docker

# Make wrapper executable
chmod +x azure-setup/az-docker.sh

# Test Azure CLI
./az-docker.sh --version
# Output: azure-cli 2.81.0
```

---

### Step 3: Azure Login and Authentication

```bash
cd azure-setup
./az-docker.sh login
```

**Login Process**:
1. Opened browser to: https://microsoft.com/devicelogin
2. Entered device code: `LE854F3L4`
3. Authenticated with: hstu.dojo@gmail.com
4. Selected subscription: "Azure for Students"

**Verification**:
```bash
./az-docker.sh account show --output table
```

**Output**:
```
EnvironmentName: AzureCloud
Name: Azure for Students
Subscription ID: 2128b63d-ecaf-42c5-bb3c-b9ba6919e10d
Tenant: Default Directory
```

**Fixed Permissions Issue**:
Azure credentials were owned by root, causing access issues:
```bash
sudo chown -R $USER:$USER ~/.azure
```

---

### Step 4: Created Deployment Scripts

**Created 5 automated deployment scripts**:

1. **`az-docker.sh`** - Docker wrapper for Azure CLI
2. **`deploy-digital-twins.sh`** - Main ADT instance and models deployment
3. **`setup-iot-routing.sh`** - Azure Function App setup
4. **`deploy-function.sh`** - Deploy Azure Function code
5. **`create-eventgrid-subscription.sh`** - IoT Hub → ADT routing
6. **`deploy-complete.sh`** - Simplified all-in-one deployment

---

### Step 5: Azure Functions Setup

**Created Azure Function for IoT Hub → Digital Twins Routing**:

**Function: `IoTHub_EventGrid`** (`azure-functions/IoTHub_EventGrid/__init__.py`)
- Trigger: Event Grid (Microsoft.Devices.DeviceTelemetry)
- Purpose: Route telemetry from IoT Hub to Digital Twins
- Updates: Device twin properties, Zone twin telemetry, AI recommendations

**Updated Dependencies** (`azure-functions/requirements.txt`):
```
azure-functions
numpy>=1.21.0
scikit-learn>=1.0.0
azure-identity>=1.12.0
azure-digitaltwins-core>=1.2.0
```

---

### Step 6: Region Selection Issues

**Challenge**: Azure Digital Twins not available in all regions.

**Attempts**:
1. ❌ `eastus` - Policy restriction (RequestDisallowedByAzure)
2. ❌ `centralindia` - Not available for Digital Twins
3. ❌ `westus2` - Initially tried
4. ✅ `southeastasia` - **Final choice** (closest to Bangladesh)

**Available Regions for Azure Digital Twins**:
- westcentralus, westus2, northeurope, australiaeast, westeurope
- eastus, southcentralus, **southeastasia**, uksouth, eastus2
- westus3, japaneast, koreacentral, qatarcentral

---

### Step 7: Fixed Script Issues

**Issue 1: Carriage Return Characters**
- Problem: Windows-style line endings (`\r\n`) in location variables
- Solution:
```bash
# Clean all scripts
for file in azure-setup/*.sh; do 
  sed -i 's/\r$//' "$file"
done

# Clean variables in commands
LOCATION=$(... | tr -d '\r\n')
```

**Issue 2: Parameter Name Mismatches**
- Azure CLI parameter inconsistencies
- Solution: Used short forms (`-n`, `-g`, `-l`) instead of long forms

**Issue 3: Script Path Resolution**
- Docker wrapper needed absolute paths
- Solution: Used `SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"`

**Issue 4: Role Propagation Delays**
- Permissions took 20-30 seconds to propagate
- Solution: Added sleep timers and retry logic

---

### Step 8: Resource Group Management

**Deleted and recreated resource group to ensure clean deployment**:

```bash
# Delete existing resource group
./az-docker.sh group delete --name adt-farm-rg --yes

# Resource group was recreated with correct location
# Location: southeastasia
```

---

### Step 9: Successful Deployment

**Final Deployment Command**:
```bash
bash azure-setup/deploy-complete.sh
```

**Deployment Steps** (Automated):

1. ✅ **Resource Group Created**
   - Name: `adt-farm-rg`
   - Location: `southeastasia`

2. ✅ **Azure Digital Twins Instance Created**
   - Name: `farm-digital-twin`
   - Endpoint: `farm-digital-twin.api.sea.digitaltwins.azure.net`
   - Provisioning State: Succeeded

3. ✅ **Role Assignment**
   - User: hstu.dojo@gmail.com (8f37faf9-ea10-4a30-ab4d-97cdd456620c)
   - Role: Azure Digital Twins Data Owner
   - Scope: ADT instance
   - Wait time: 20 seconds for propagation

4. ✅ **DTDL Models Uploaded**
   - dtmi:agriculture:Farm;1
   - dtmi:agriculture:Crop;1
   - dtmi:agriculture:Zone;1
   - dtmi:agriculture:Device;1

5. ✅ **Digital Twins Created**
   - `farm_001` (Farm) - Research Farm, Dhaka
   - `rice` (Crop) - Oryza sativa, Monsoon season
   - `wheat` (Crop) - Triticum aestivum, Winter season
   - `maize` (Crop) - Zea mays, Summer season
   - `zone_A` (Zone) - 2.5 hectares, Clay Loam soil
   - `pc_sim_01` (Device) - Environment Sensor

6. ✅ **Relationships Created**
   - farm_001 → hasZone → zone_A
   - zone_A → hasDevice → pc_sim_01
   - zone_A → growsCrop → rice

---

## Final Configuration

### Azure Resources Created

| Resource | Name | Location | Status |
|----------|------|----------|--------|
| Resource Group | adt-farm-rg | Southeast Asia | Active |
| Digital Twins Instance | farm-digital-twin | Southeast Asia | Succeeded |
| Storage Account | adtfuncstorage* | Southeast Asia | Pending |
| Function App | adt-telemetry-router | Southeast Asia | Pending |

### Digital Twin Graph Structure

```
farm_001 (Farm)
    ↓ hasZone
zone_A (Zone)
    ↓ hasDevice        ↓ growsCrop
pc_sim_01 (Device)   rice (Crop)

Crops in catalog: rice, wheat, maize
```

---

## Access Information

### Digital Twin Explorer
- URL: https://explorer.digitaltwins.azure.net/
- Instance: `farm-digital-twin`
- Endpoint: `https://farm-digital-twin.api.sea.digitaltwins.azure.net`

### Azure Portal
- Subscription: Azure for Students
- Resource Group: adt-farm-rg
- Location: Southeast Asia (Singapore)

---

## Next Steps (Pending)

1. **Run IoT Hub Routing Setup**:
   ```bash
   ./azure-setup/setup-iot-routing.sh
   ```
   - Creates Azure Function App
   - Sets up managed identity
   - Configures environment variables

2. **Deploy Azure Function**:
   ```bash
   ./azure-setup/deploy-function.sh
   ```
   - Deploys IoTHub_EventGrid function
   - Deploys AI_Inference function

3. **Create Event Grid Subscription**:
   ```bash
   ./azure-setup/create-eventgrid-subscription.sh
   ```
   - Routes IoT Hub telemetry → Azure Function → Digital Twins

4. **Test End-to-End Flow**:
   - Node-RED sends telemetry to IoT Hub
   - Event Grid triggers Azure Function
   - Function updates Digital Twins
   - View real-time updates in Digital Twin Explorer

---

## Commands Reference

### Verify Deployment
```bash
# List models
./az-docker.sh dt model list -n farm-digital-twin --output table

# List twins
./az-docker.sh dt twin query -n farm-digital-twin \
  --query-command "SELECT * FROM digitaltwins"

# View specific twin
./az-docker.sh dt twin show -n farm-digital-twin --twin-id zone_A

# Check relationships
./az-docker.sh dt twin relationship list -n farm-digital-twin \
  --twin-id zone_A
```

### Troubleshooting
```bash
# Check ADT instance status
./az-docker.sh dt show -n farm-digital-twin -g adt-farm-rg

# View role assignments
./az-docker.sh dt role-assignment list -n farm-digital-twin

# Test Function App
curl -X POST "https://adt-telemetry-router.azurewebsites.net/api/predict" \
  -H "Content-Type: application/json" \
  -d '{"temperature": 28.5, "humidity": 75.0, "soilMoisture": 65.0}'
```

---

## File Structure

```
adt/
├── azure-setup/
│   ├── az-docker.sh                          # Docker wrapper for Azure CLI
│   ├── deploy-complete.sh                    # All-in-one deployment (NEW)
│   ├── deploy-digital-twins.sh               # ADT instance + models + twins
│   ├── setup-iot-routing.sh                  # Function App setup
│   ├── deploy-function.sh                    # Function deployment
│   ├── create-eventgrid-subscription.sh      # Event Grid routing
│   └── README.md                             # Deployment guide
├── digital-twins/
│   └── models/
│       ├── Farm.json                         # Farm DTDL model
│       ├── Zone.json                         # Zone DTDL model
│       ├── Device.json                       # Device DTDL model
│       └── Crop.json                         # Crop DTDL model
├── azure-functions/
│   ├── IoTHub_EventGrid/
│   │   ├── __init__.py                       # Event Grid trigger function
│   │   └── function.json                     # Function bindings
│   ├── AI_Inference/
│   │   ├── __init__.py                       # HTTP inference endpoint
│   │   └── function.json                     # HTTP trigger config
│   ├── requirements.txt                      # Python dependencies
│   └── host.json                             # Function App config
└── simulation/
    ├── flows.json                            # Node-RED flows
    ├── Dockerfile                            # Docker container config
    └── generate_sas_token.py                 # IoT Hub auth
```

---

## Key Learnings

1. **Docker as Azure CLI Solution**: Most reliable method for Arch Linux
2. **Role Propagation**: Always wait 20-30 seconds after role assignment
3. **Region Restrictions**: Student subscriptions have limited region access
4. **Line Endings**: Windows-style `\r\n` breaks Azure CLI commands
5. **ANSI Escape Codes**: Docker output includes escape sequences - must clean with `tr -d '\r\n' | sed`

---

## Cost Estimation

| Service | Usage | Cost (Monthly) |
|---------|-------|----------------|
| Azure Digital Twins | Standard tier | ~$30-40 |
| Azure Function App | Consumption plan | ~$0-5 |
| Storage Account | Standard LRS | ~$0.50 |
| Event Grid | Per event | ~$0.60/million |
| **Total** | | **~$31-46** |

---

## Session Statistics

- **Time**: ~2 hours
- **Scripts Created**: 6
- **Models Created**: 4
- **Digital Twins Created**: 6
- **Relationships Created**: 3
- **Docker Images Pulled**: 1 (Azure CLI)
- **Commands Executed**: 100+
- **Issues Resolved**: 8

---

## Status: ✅ DEPLOYMENT COMPLETE (Phase 4-5)

Azure Digital Twins infrastructure is now deployed and ready for:
- Real-time telemetry ingestion from IoT Hub
- AI-powered crop recommendations
- Digital Twin Explorer visualization
- Advanced queries and analytics

**Completed**: December 16, 2025
**Next Session**: Phase 6 - IoT Hub routing, Function deployment, and real-time data visualization (December 17, 2025)

---

## How to Run This Project

### Prerequisites
- Docker installed and running
- Azure account with active subscription
- Git repository cloned locally

### GitHub Repository
- **Repository**: https://github.com/hasanshahriar32/adt-node
- **Branch**: main
- **Clone Command**:
  ```bash
  git clone https://github.com/hasanshahriar32/adt-node.git
  cd adt-node
  ```

### Quick Start Guide

#### 1. Initial Setup (Azure CLI via Docker)
```bash
# Navigate to azure-setup directory
cd azure-setup

# Start Docker daemon (if not running)
sudo systemctl start docker
sudo systemctl enable docker

# Make scripts executable
chmod +x *.sh

# Test Azure CLI
./az-docker.sh --version

# Login to Azure
./az-docker.sh login
# Follow browser prompts to authenticate
```

#### 2. Deploy Azure Digital Twins (Complete Setup)
```bash
# Run the all-in-one deployment script
bash deploy-complete.sh
```

**This script automatically**:
- Creates resource group in Southeast Asia
- Deploys Azure Digital Twins instance
- Assigns permissions
- Uploads 4 DTDL models
- Creates 6 digital twins
- Establishes 3 relationships

**Expected Duration**: 5-7 minutes

#### 3. Verify Deployment
```bash
# List all digital twins
./az-docker.sh dt twin query -n farm-digital-twin \
  --query-command "SELECT * FROM digitaltwins"

# Check specific twin
./az-docker.sh dt twin show -n farm-digital-twin --twin-id zone_A

# View models
./az-docker.sh dt model list -n farm-digital-twin --output table
```

#### 4. Access Digital Twin Explorer
1. Open browser: https://explorer.digitaltwins.azure.net/
2. Sign in with Azure account
3. Select instance: `farm-digital-twin`
4. View your digital twin graph

#### 5. Deploy Azure Functions (IoT Hub Routing)
```bash
# Setup Function App and IoT routing
bash setup-iot-routing.sh

# Deploy function code
bash deploy-function.sh

# Create Event Grid subscription
bash create-eventgrid-subscription.sh
```

#### 6. Start Node-RED Simulation
```bash
# Navigate to simulation directory
cd ../simulation

# Start Node-RED (locally or via Docker)
docker-compose up -d

# Access Node-RED UI
# Open: http://localhost:1880
```

---

## Files You Need to Run

### Essential Scripts (Must Run in Order)

| Order | File | Location | Purpose | Command |
|-------|------|----------|---------|---------|
| 1 | `az-docker.sh` | `azure-setup/` | Azure CLI wrapper | `./az-docker.sh login` |
| 2 | `deploy-complete.sh` | `azure-setup/` | **MAIN DEPLOYMENT** | `bash deploy-complete.sh` |
| 3 | `setup-iot-routing.sh` | `azure-setup/` | Function App setup | `bash setup-iot-routing.sh` |
| 4 | `deploy-function.sh` | `azure-setup/` | Deploy Functions | `bash deploy-function.sh` |
| 5 | `create-eventgrid-subscription.sh` | `azure-setup/` | IoT → ADT routing | `bash create-eventgrid-subscription.sh` |

### Configuration Files (Auto-loaded by scripts)

| File | Location | Purpose | Used By |
|------|----------|---------|---------|
| `Farm.json` | `digital-twins/models/` | Farm DTDL model | deploy-complete.sh |
| `Zone.json` | `digital-twins/models/` | Zone DTDL model | deploy-complete.sh |
| `Device.json` | `digital-twins/models/` | Device DTDL model | deploy-complete.sh |
| `Crop.json` | `digital-twins/models/` | Crop DTDL model | deploy-complete.sh |
| `__init__.py` | `azure-functions/IoTHub_EventGrid/` | Event Grid handler | deploy-function.sh |
| `__init__.py` | `azure-functions/AI_Inference/` | AI inference API | deploy-function.sh |
| `requirements.txt` | `azure-functions/` | Python dependencies | deploy-function.sh |

### Node-RED Files (For Simulation)

| File | Location | Purpose |
|------|----------|---------|
| `flows.json` | `simulation/` | Node-RED flow definition |
| `generate_sas_token.py` | `simulation/` | IoT Hub authentication |
| `Dockerfile` | `simulation/` | Container configuration |
| `start_simulation.sh` | `simulation/` | Startup script |

---

## GitHub Repository Structure

```
hasanshahriar32/adt-node (main)
│
├── azure-setup/                              ← START HERE
│   ├── az-docker.sh                         ← Run first (login)
│   ├── deploy-complete.sh                   ← Run second (main deployment)
│   ├── setup-iot-routing.sh                 ← Run third
│   ├── deploy-function.sh                   ← Run fourth
│   ├── create-eventgrid-subscription.sh     ← Run fifth
│   ├── deploy-digital-twins.sh              (deprecated, use deploy-complete.sh)
│   └── README.md                            ← Deployment instructions
│
├── digital-twins/
│   └── models/                              ← DTDL Models (auto-loaded)
│       ├── Farm.json
│       ├── Zone.json
│       ├── Device.json
│       └── Crop.json
│
├── azure-functions/                         ← Azure Function code
│   ├── IoTHub_EventGrid/
│   │   ├── __init__.py                      ← Telemetry routing logic
│   │   └── function.json
│   ├── AI_Inference/
│   │   ├── __init__.py                      ← ML inference endpoint
│   │   └── function.json
│   ├── requirements.txt                     ← Python dependencies
│   └── host.json
│
├── simulation/                              ← Node-RED simulation
│   ├── flows.json                           ← Flow configuration
│   ├── generate_sas_token.py               ← IoT Hub auth
│   ├── Dockerfile                           ← Container setup
│   └── start_simulation.sh                  ← Startup script
│
├── docs/
│   └── AI_INTEGRATION.md                    ← AI architecture guide
│
├── PROGRESS.md                              ← Phase 1-3 documentation
├── SESSION_DOCUMENTATION.md                 ← This file
└── README.md                                ← Project overview
```

---

## Step-by-Step Execution Guide

### Scenario 1: Fresh Deployment (First Time)

```bash
# 1. Clone repository
git clone https://github.com/hasanshahriar32/adt-node.git
cd adt-node

# 2. Start Docker
sudo systemctl start docker

# 3. Navigate to azure-setup
cd azure-setup

# 4. Make scripts executable
chmod +x *.sh

# 5. Login to Azure
./az-docker.sh login
# Complete authentication in browser

# 6. Deploy everything
bash deploy-complete.sh
# Wait 5-7 minutes for completion

# 7. Verify deployment
./az-docker.sh dt twin query -n farm-digital-twin \
  --query-command "SELECT * FROM digitaltwins"

# 8. Access Digital Twin Explorer
# Open: https://explorer.digitaltwins.azure.net/
# Select instance: farm-digital-twin
```

### Scenario 2: Update Existing Deployment

```bash
# Pull latest changes
git pull origin main

# Navigate to azure-setup
cd azure-setup

# Option A: Update models only
./az-docker.sh dt model create -n farm-digital-twin \
  --models ../digital-twins/models/Zone.json

# Option B: Redeploy completely
./az-docker.sh dt delete -n farm-digital-twin -g adt-farm-rg -y
bash deploy-complete.sh
```

### Scenario 3: Deploy Functions & IoT Routing

```bash
# After Digital Twins deployment is complete

cd azure-setup

# 1. Setup Function App
bash setup-iot-routing.sh
# Creates Function App, Storage Account, assigns roles

# 2. Deploy function code
bash deploy-function.sh
# Packages and deploys Python functions

# 3. Connect IoT Hub to Digital Twins
bash create-eventgrid-subscription.sh
# Creates Event Grid subscription
```

### Scenario 4: Test End-to-End Flow

```bash
# 1. Ensure Azure setup is complete (above steps)

# 2. Start Node-RED simulation
cd ../simulation
docker-compose up -d

# 3. Open Node-RED UI
# Browser: http://localhost:1880/ui

# 4. Deploy flows
# Browser: http://localhost:1880
# Click "Deploy" button

# 5. Monitor telemetry
# Node-RED UI shows real-time sensor data

# 6. View in Digital Twin Explorer
# https://explorer.digitaltwins.azure.net/
# Watch zone_A twin update with telemetry
```

---

## Troubleshooting

### Issue: Azure CLI not found
```bash
# Solution: Ensure Docker is running
sudo systemctl start docker
./az-docker.sh --version
```

### Issue: Permission denied on scripts
```bash
# Solution: Make scripts executable
chmod +x azure-setup/*.sh
```

### Issue: Role assignment failed
```bash
# Solution: Wait 30 seconds and retry
sleep 30
bash deploy-complete.sh
```

### Issue: Models won't upload
```bash
# Solution: Check role propagation
./az-docker.sh dt role-assignment list -n farm-digital-twin
# Wait 20 seconds if no assignments shown
```

### Issue: Twin already exists
```bash
# Solution: Delete and recreate
./az-docker.sh dt twin delete -n farm-digital-twin \
  --twin-id zone_A -y
# Then re-run deploy-complete.sh
```

---

## Quick Reference Commands

```bash
# Check login status
./az-docker.sh account show

# List all twins
./az-docker.sh dt twin query -n farm-digital-twin \
  --query-command "SELECT * FROM digitaltwins"

# View specific twin with relationships
./az-docker.sh dt twin show -n farm-digital-twin \
  --twin-id zone_A

# Update twin property
./az-docker.sh dt twin update -n farm-digital-twin \
  --twin-id zone_A \
  --json-patch '[{"op":"replace","path":"/recommendedCrop","value":"wheat"}]'

# View telemetry (requires Time Series Insights or queries)
./az-docker.sh dt twin query -n farm-digital-twin \
  --query-command "SELECT * FROM digitaltwins WHERE \$dtId = 'zone_A'"

# Clean up all resources
./az-docker.sh group delete --name adt-farm-rg --yes
```

---

## Files Required from GitHub

### Minimum Files to Run:
1. `azure-setup/az-docker.sh` ⭐ **CRITICAL**
2. `azure-setup/deploy-complete.sh` ⭐ **CRITICAL**
3. `digital-twins/models/*.json` (all 4 files) ⭐ **CRITICAL**
4. `azure-functions/**/*` (for IoT routing)
5. `simulation/**/*` (for Node-RED)

### Download Only Essential Files:
```bash
# If you don't want to clone the entire repo:
cd /tmp
git clone --depth 1 --filter=blob:none --sparse \
  https://github.com/hasanshahriar32/adt-node.git
cd adt-node
git sparse-checkout set azure-setup digital-twins/models azure-functions
```

---

## Repository Links

- **Main Repository**: https://github.com/hasanshahriar32/adt-node
- **Azure Setup Scripts**: https://github.com/hasanshahriar32/adt-node/tree/main/azure-setup
- **DTDL Models**: https://github.com/hasanshahriar32/adt-node/tree/main/digital-twins/models
- **Azure Functions**: https://github.com/hasanshahriar32/adt-node/tree/main/azure-functions
- **Node-RED Simulation**: https://github.com/hasanshahriar32/adt-node/tree/main/simulation
