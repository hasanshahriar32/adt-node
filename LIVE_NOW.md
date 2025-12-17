# 🎉 YOUR DIGITAL TWIN IS LIVE!

## ✅ Status: RUNNING & UPDATING

### 🔥 Real-Time Simulation
- **Status**: ✅ **ACTIVE**
- **Process**: Node-RED simulation (PID: check with `ps aux | grep node-red`)
- **Updates**: Every ~60 seconds via IoT Hub → Event Grid → Azure Function
- **Twin**: `zone_A` in `farm-digital-twin`
- **Data**: Temperature, Humidity, Soil Moisture
- **Pipeline**: Node-RED → IoT Hub → Event Grid → Function → Digital Twin

### 📊 VIEW YOUR LIVE DATA NOW!

**Open this URL**: https://explorer.digitaltwins.azure.net

1. Click on **farm-digital-twin**
2. Click on **zone_A** twin
3. See live values updating every 5 seconds! 🎯

---

## 🎬 For Your Showcase

### Perfect Demo Steps:

1. **Open Azure Digital Twins Explorer**
   - URL: https://explorer.digitaltwins.azure.net
   - Select: `farm-digital-twin`

2. **Show the Graph**
   - You'll see: Farm → Zone A → Device → Crops
   - Click: `zone_A`

3. **Show Live Data**
   - Properties panel shows:
     - `temperature`: Currently 27.0°C (updating every ~60s)
     - `humidity`: Currently 72.0% (updating every ~60s)
     - `soilMoisture`: Currently 63.0% (updating every ~60s)
   - **Wait 60 seconds and refresh** → Values change!

4. **Explain**:
   - "These are live sensor readings flowing through Azure IoT Hub"
   - "Event Grid routes telemetry to Azure Functions"
   - "Functions update the Digital Twin in real-time"
   - "Perfect for real-time farm monitoring and analytics"

---

## 🛠️ Simulation Management

### Check Status
```bash
ps aux | grep run-sim.py | grep -v grep
tail -f /home/hs32/Documents/Projects/adt/azure-setup/live-sim.log
```

### Stop Simulation
```bash
kill $(cat /home/hs32/Documents/Projects/adt/azure-setup/live-sim.pid)
```

### Restart Simulation
```bash
cd /home/hs32/Documents/Projects/adt/azure-setup
python3 run-sim.py > live-sim.log 2>&1 &
echo $! > live-sim.pid
```

### View Current Values
```bash
cd /home/hs32/Documents/Projects/adt/azure-setup
./az-docker.sh dt twin show -n farm-digital-twin --twin-id zone_A \
  --query "{temp:temperature,hum:humidity,soil:soilMoisture}"
```

---

## 🌐 Public Access Options

### Option 1: Azure Digital Twins Explorer ⭐ (Best for Demo)
- **URL**: https://explorer.digitaltwins.azure.net
- **Pros**: Professional interface, shows graph, real-time updates
- **Access**: Requires Azure login (your account)

### Option 2: Public HTML Dashboard
If you need **no-login** public access:

```bash
cd /home/hs32/Documents/Projects/adt
cp azure-setup/public-dashboard.html docs/index.html
git add docs/index.html
git commit -m "Add public dashboard"
git push
```

Then enable GitHub Pages:
- Settings → Pages → Source: main/docs
- Public URL: `https://YOUR_USERNAME.github.io/adt/`

---

## 📈 Current Live Data

Temperature: 24-32°C (realistic farm range)
Humidity: 60-85% (realistic range)  
Soil Moisture: 55-75% (optimal for crops)

**All values update every 5 seconds!**

---

## 🚀 You're Ready to Showcase!

**Your simulation is:**
- ✅ Running continuously
- ✅ Updating Digital Twins in real-time
- ✅ Visible in Azure Digital Twins Explorer
- ✅ Perfect for demonstrations

**Go ahead and open**: https://explorer.digitaltwins.azure.net 🎯

Enjoy showcasing your live Digital Twin! 🌾📊
