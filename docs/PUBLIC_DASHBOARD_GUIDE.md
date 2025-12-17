# 🌾 Public Dashboard Setup Guide

## ✅ Current Status

### Simulation Running
- **Status**: ✅ Active
- **PID**: Check with `cat /home/hs32/Documents/Projects/adt/azure-setup/sim.pid`
- **Updates**: Every 5 seconds
- **Twins Updated**: `zone_A` and `pc_sim_01`

### Monitor Simulation
```bash
# View live updates
cd /home/hs32/Documents/Projects/adt/azure-setup
tail -f sim-output.log

# Stop simulation
kill $(cat sim.pid)

# Restart simulation
./sim.sh > sim-output.log 2>&1 & echo $! > sim.pid
```

### Verify Data in Azure
```bash
cd /home/hs32/Documents/Projects/adt/azure-setup

# Check zone_A twin
./az-docker.sh dt twin show -n farm-digital-twin --twin-id zone_A

# Query all twins with sensor data
./az-docker.sh dt twin query -n farm-digital-twin \
  --query-command "SELECT * FROM digitaltwins WHERE IS_DEFINED(temperature)"
```

## 📊 Public Dashboard Options

### Option 1: Azure Digital Twins Explorer (Recommended for Demo)

**URL**: https://explorer.digitaltwins.azure.net

**Steps**:
1. Open https://explorer.digitaltwins.azure.net
2. Sign in with your Azure account
3. Select **farm-digital-twin** instance
4. You'll see your twins graph:
   - Farm → Zones → Devices → Crops
5. Click on **zone_A** to see live sensor values
6. The data updates in real-time!

**For Showcase**:
- Click on `zone_A` twin
- Properties panel shows: temperature, humidity, soilMoisture
- Values update every 5 seconds from simulation
- Professional Azure interface, perfect for presentations

### Option 2: Custom Public Dashboard (HTML)

**Location**: `/home/hs32/Documents/Projects/adt/azure-setup/public-dashboard.html`

**Deployment Options**:

#### A) GitHub Pages (Free, Public)
```bash
cd /home/hs32/Documents/Projects/adt

# Copy dashboard to docs folder
cp azure-setup/public-dashboard.html docs/index.html

# Commit and push
git add docs/index.html
git commit -m "Add public dashboard"
git push

# Then enable GitHub Pages:
# 1. Go to repository Settings → Pages
# 2. Source: Deploy from branch
# 3. Branch: main, Folder: /docs
# 4. Save

# Your public URL will be:
# https://YOUR_USERNAME.github.io/adt/
```

#### B) Azure Static Web Apps
```bash
cd /home/hs32/Documents/Projects/adt/azure-setup

./az-docker.sh staticwebapp create \
  --name farm-dashboard \
  --resource-group adt-farm-rg \
  --source azure-setup/public-dashboard.html \
  --location eastasia \
  --sku Free

# Get the URL
./az-docker.sh staticwebapp show \
  --name farm-dashboard \
  -g adt-farm-rg \
  --query "defaultHostname" -o tsv
```

#### C) Simple Python HTTP Server (Quick Test)
```bash
cd /home/hs32/Documents/Projects/adt/azure-setup
python3 -m http.server 8080

# Open: http://YOUR_IP:8080/public-dashboard.html
# Or if local: http://localhost:8080/public-dashboard.html
```

### Option 3: API Access (For Developers)

**Public API Endpoint**:
```
https://adt-telemetry-router.azurewebsites.net/api/getTwinData
```

**Test**:
```bash
curl https://adt-telemetry-router.azurewebsites.net/api/getTwinData | python3 -m json.tool
```

**Response** (example):
```json
{
  "twins": [
    {
      "$dtId": "zone_A",
      "temperature": 28.5,
      "humidity": 72.3,
      "soilMoisture": 65.8,
      "lastUpdated": "2025-12-16T19:42:48Z"
    },
    {
      "$dtId": "pc_sim_01",
      "temperature": 28.5,
      "humidity": 72.3,
      "soilMoisture": 65.8,
      "status": "active"
    }
  ]
}
```

## 🎯 Recommended Setup for Showcase

### Best Option: Azure Digital Twins Explorer

**Why?**
- ✅ Professional Microsoft Azure interface
- ✅ Real-time updates visible
- ✅ Graph visualization of relationships
- ✅ No additional hosting needed
- ✅ Can click through twins to see all properties
- ✅ Shows metadata and relationships

**How to Present**:
1. Open https://explorer.digitaltwins.azure.net
2. Select `farm-digital-twin`
3. Show the graph: Farm → Zone A → Device → Crop
4. Click `zone_A` → See live temperature, humidity, soil moisture
5. Explain: "This data is coming from our simulation in real-time"
6. Refresh or wait 5 seconds → Values change!

### Alternative: Quick Public Dashboard

If you need a custom interface without Azure login:

1. **Deploy to GitHub Pages** (5 minutes):
   ```bash
   cp azure-setup/public-dashboard.html docs/index.html
   git add docs/index.html && git commit -m "Public dashboard" && git push
   ```
   
2. **Enable in GitHub**:
   - Settings → Pages → Source: main/docs
   
3. **Share URL**:
   - `https://YOUR_USERNAME.github.io/adt/`

## 🔧 Troubleshooting

### Simulation Not Running
```bash
cd /home/hs32/Documents/Projects/adt/azure-setup
ps aux | grep sim.sh | grep -v grep

# If not running, restart:
./sim.sh > sim-output.log 2>&1 & echo $! > sim.pid
```

### API Returns Empty Data
The Azure Function needs role assignment (propagation takes 10-15 min). Use Azure Digital Twins Explorer instead - it works immediately!

### Cannot See Updates in Explorer
1. Ensure simulation is running: `tail -f azure-setup/sim-output.log`
2. Click refresh icon in Explorer
3. Click on zone_A twin
4. Check "temperature" property value
5. Wait 5 seconds and check again - value should change

## 📝 Summary

**For Showcase** ✅:
- Simulation: **Running** (updates every 5 seconds)
- Best Viewer: **Azure Digital Twins Explorer**
- URL: https://explorer.digitaltwins.azure.net
- Instance: `farm-digital-twin`
- Live Twins: `zone_A`, `pc_sim_01`

**Live Data** ✅:
- Temperature: 24-32°C (changes every 5s)
- Humidity: 60-85% (changes every 5s)
- Soil Moisture: 55-75% (changes every 5s)

**Perfect for Demo!** 🎉
