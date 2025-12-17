# Public-Facing Digital Twin Interface Options

## 🎯 Goal
Create a public-accessible interface where visitors can view **live IoT telemetry data** from your agricultural digital twin system without needing authentication or Azure access.

---

## 📊 Current System Status

### ✅ What You Have Working:
1. **Node-RED Simulation** → Generating live telemetry at http://localhost:1880
2. **API Endpoint** → `/api/telemetry` serving JSON data at https://adt-node.onrender.com/api/telemetry
3. **Streamlit Dashboard** → AI predictions at http://localhost:8501
4. **Azure IoT Hub** → Receiving telemetry (if configured)

### 🎨 What You Want:
A **Digital Twin Explorer-style interface** that shows:
- Live sensor data visualization
- 3D/2D farm layout
- Real-time charts and graphs
- Interactive twin property explorer
- Public access (no login required)

---

## 🛠️ Solution Options

### **Option 1: Azure Digital Twins Explorer (Open Source) - Modified**

**Repository**: https://github.com/Azure-Samples/digital-twins-explorer

#### **Pros:**
- ✅ Official Microsoft tool
- ✅ Professional 3D visualization
- ✅ Built for Azure Digital Twins
- ✅ Open source (MIT license)

#### **Cons:**
- ❌ Requires Azure AD authentication by default
- ❌ Needs Azure Digital Twins instance
- ❌ Complex setup

#### **How to Deploy (Modified for Public Access):**

1. **Clone the repo:**
```bash
cd /home/hs32/Documents/Projects/adt
git clone https://github.com/Azure-Samples/digital-twins-explorer.git
cd digital-twins-explorer/client
```

2. **Install dependencies:**
```bash
npm install
```

3. **Modify for public access (Remove Auth):**

Create custom proxy endpoint that doesn't require Azure AD:

```javascript
// client/src/proxy.js (create this file)
const express = require('express');
const axios = require('axios');
const app = express();

app.use(express.json());

// Proxy endpoint for your API
app.get('/api/telemetry', async (req, res) => {
  try {
    const response = await axios.get('https://adt-node.onrender.com/api/telemetry');
    res.json(response.data);
  } catch (error) {
    res.status(500).json({ error: 'Failed to fetch telemetry' });
  }
});

app.listen(3001, () => {
  console.log('Proxy running on http://localhost:3001');
});
```

4. **Build and deploy:**
```bash
npm run build
# Deploy to GitHub Pages, Netlify, or Vercel
```

---

### **Option 2: Custom 3D Web Dashboard (Recommended) ⭐**

Build a lightweight custom dashboard using modern web technologies.

#### **Stack:**
- **Frontend**: React + Three.js (3D visualization)
- **Charts**: Plotly.js or Chart.js
- **Real-time**: WebSocket or SSE (Server-Sent Events)
- **Backend**: Your existing Node-RED API

#### **Quick Start Template:**

**File Structure:**
```
public-twin-interface/
├── index.html
├── app.js
├── style.css
└── package.json
```

**index.html:**
```html
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Agricultural Digital Twin - Live Monitor</title>
    <script src="https://cdn.plot.ly/plotly-2.27.0.min.js"></script>
    <script src="https://unpkg.com/three@0.160.0/build/three.min.js"></script>
    <link rel="stylesheet" href="style.css">
</head>
<body>
    <div class="container">
        <header>
            <h1>🌾 Agricultural Digital Twin - Live Monitor</h1>
            <p>Real-time IoT Telemetry from Farm Sensors</p>
        </header>

        <div class="dashboard">
            <!-- Live Metrics -->
            <div class="metrics-grid">
                <div class="metric-card">
                    <h3>🌡️ Temperature</h3>
                    <div class="value" id="temp-value">-- °C</div>
                    <div class="timestamp" id="temp-time">--</div>
                </div>
                <div class="metric-card">
                    <h3>💧 Humidity</h3>
                    <div class="value" id="hum-value">-- %</div>
                    <div class="timestamp" id="hum-time">--</div>
                </div>
                <div class="metric-card">
                    <h3>🌱 Soil Moisture</h3>
                    <div class="value" id="soil-value">-- %</div>
                    <div class="timestamp" id="soil-time">--</div>
                </div>
                <div class="metric-card">
                    <h3>📍 Device Status</h3>
                    <div class="value" id="status-value">ONLINE</div>
                    <div class="timestamp" id="device-id">--</div>
                </div>
            </div>

            <!-- Charts -->
            <div class="charts-container">
                <div class="chart-wrapper">
                    <h3>Temperature History</h3>
                    <div id="temp-chart"></div>
                </div>
                <div class="chart-wrapper">
                    <h3>Humidity & Soil Moisture</h3>
                    <div id="moisture-chart"></div>
                </div>
            </div>

            <!-- 3D Farm Visualization -->
            <div class="visualization">
                <h3>3D Farm Layout</h3>
                <div id="3d-canvas"></div>
            </div>

            <!-- Raw Data -->
            <div class="raw-data">
                <h3>Latest Telemetry Packet</h3>
                <pre id="raw-json">Waiting for data...</pre>
            </div>
        </div>
    </div>

    <script src="app.js"></script>
</body>
</html>
```

**app.js:**
```javascript
// Configuration
const API_URL = 'https://adt-node.onrender.com/api/telemetry';
const REFRESH_INTERVAL = 5000; // 5 seconds

// Data storage for charts
let temperatureData = {
    x: [],
    y: [],
    type: 'scatter',
    mode: 'lines+markers',
    name: 'Temperature',
    line: { color: '#FF6B6B' }
};

let humidityData = {
    x: [],
    y: [],
    type: 'scatter',
    mode: 'lines+markers',
    name: 'Humidity',
    line: { color: '#4ECDC4' },
    yaxis: 'y1'
};

let soilData = {
    x: [],
    y: [],
    type: 'scatter',
    mode: 'lines+markers',
    name: 'Soil Moisture',
    line: { color: '#95B46A' },
    yaxis: 'y1'
};

// Initialize charts
function initCharts() {
    Plotly.newPlot('temp-chart', [temperatureData], {
        margin: { t: 10, r: 20, b: 40, l: 60 },
        xaxis: { title: 'Time' },
        yaxis: { title: 'Temperature (°C)' },
        plot_bgcolor: '#F1F8E9',
        paper_bgcolor: '#FFFFFF'
    });

    Plotly.newPlot('moisture-chart', [humidityData, soilData], {
        margin: { t: 10, r: 20, b: 40, l: 60 },
        xaxis: { title: 'Time' },
        yaxis: { title: 'Percentage (%)' },
        plot_bgcolor: '#F1F8E9',
        paper_bgcolor: '#FFFFFF'
    });
}

// Initialize 3D scene
function init3DScene() {
    const canvas = document.getElementById('3d-canvas');
    const scene = new THREE.Scene();
    scene.background = new THREE.Color(0xE8F5E9);
    
    const camera = new THREE.PerspectiveCamera(75, canvas.clientWidth / canvas.clientHeight, 0.1, 1000);
    const renderer = new THREE.WebGLRenderer({ antialias: true });
    
    renderer.setSize(canvas.clientWidth, 400);
    canvas.appendChild(renderer.domElement);

    // Add farm field (green plane)
    const fieldGeometry = new THREE.PlaneGeometry(20, 20);
    const fieldMaterial = new THREE.MeshBasicMaterial({ color: 0x7CB342, side: THREE.DoubleSide });
    const field = new THREE.Mesh(fieldGeometry, fieldMaterial);
    field.rotation.x = -Math.PI / 2;
    scene.add(field);

    // Add sensor node (glowing sphere)
    const sensorGeometry = new THREE.SphereGeometry(0.5, 32, 32);
    const sensorMaterial = new THREE.MeshBasicMaterial({ color: 0x2196F3 });
    const sensor = new THREE.Mesh(sensorGeometry, sensorMaterial);
    sensor.position.set(0, 0.5, 0);
    scene.add(sensor);

    // Add ambient light
    const light = new THREE.AmbientLight(0xffffff, 0.8);
    scene.add(light);

    camera.position.set(5, 5, 5);
    camera.lookAt(0, 0, 0);

    // Animation loop
    function animate() {
        requestAnimationFrame(animate);
        sensor.rotation.y += 0.01;
        renderer.render(scene, camera);
    }
    animate();
}

// Fetch telemetry data
async function fetchTelemetry() {
    try {
        const response = await fetch(API_URL);
        const data = await response.json();
        
        updateMetrics(data);
        updateCharts(data);
        updateRawData(data);
    } catch (error) {
        console.error('Error fetching telemetry:', error);
        document.getElementById('status-value').textContent = 'OFFLINE';
        document.getElementById('status-value').style.color = '#F44336';
    }
}

// Update metric cards
function updateMetrics(data) {
    const now = new Date().toLocaleTimeString();
    
    if (data.telemetry) {
        document.getElementById('temp-value').textContent = 
            `${data.telemetry.temperature?.toFixed(1) || '--'} °C`;
        document.getElementById('hum-value').textContent = 
            `${data.telemetry.humidity?.toFixed(1) || '--'} %`;
        document.getElementById('soil-value').textContent = 
            `${data.telemetry.soilMoisture?.toFixed(1) || '--'} %`;
        
        document.getElementById('temp-time').textContent = now;
        document.getElementById('hum-time').textContent = now;
        document.getElementById('soil-time').textContent = now;
    }
    
    if (data.deviceId) {
        document.getElementById('device-id').textContent = data.deviceId;
    }
    
    document.getElementById('status-value').textContent = 'ONLINE';
    document.getElementById('status-value').style.color = '#4CAF50';
}

// Update charts with new data
function updateCharts(data) {
    if (!data.telemetry) return;

    const now = new Date();
    
    // Keep only last 20 data points
    if (temperatureData.x.length > 20) {
        temperatureData.x.shift();
        temperatureData.y.shift();
        humidityData.x.shift();
        humidityData.y.shift();
        soilData.x.shift();
        soilData.y.shift();
    }
    
    temperatureData.x.push(now);
    temperatureData.y.push(data.telemetry.temperature);
    
    humidityData.x.push(now);
    humidityData.y.push(data.telemetry.humidity);
    
    soilData.x.push(now);
    soilData.y.push(data.telemetry.soilMoisture);
    
    Plotly.react('temp-chart', [temperatureData]);
    Plotly.react('moisture-chart', [humidityData, soilData]);
}

// Update raw JSON display
function updateRawData(data) {
    document.getElementById('raw-json').textContent = JSON.stringify(data, null, 2);
}

// Initialize everything
window.addEventListener('DOMContentLoaded', () => {
    initCharts();
    init3DScene();
    fetchTelemetry(); // Initial fetch
    setInterval(fetchTelemetry, REFRESH_INTERVAL); // Poll every 5 seconds
});
```

**style.css:**
```css
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

body {
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
    background: linear-gradient(135deg, #F1F8E9 0%, #DCEDC8 50%, #C5E1A5 100%);
    min-height: 100vh;
    padding: 20px;
}

.container {
    max-width: 1400px;
    margin: 0 auto;
}

header {
    background: linear-gradient(135deg, #558B2F 0%, #689F38 100%);
    color: white;
    padding: 2rem;
    border-radius: 15px;
    text-align: center;
    margin-bottom: 2rem;
    box-shadow: 0 4px 20px rgba(85, 139, 47, 0.3);
}

header h1 {
    font-size: 2.5rem;
    margin-bottom: 0.5rem;
}

header p {
    font-size: 1.2rem;
    opacity: 0.95;
}

.dashboard {
    display: grid;
    gap: 20px;
}

.metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 20px;
}

.metric-card {
    background: linear-gradient(135deg, #FFFFFF 0%, #F1F8E9 100%);
    padding: 1.5rem;
    border-radius: 12px;
    box-shadow: 0 3px 10px rgba(139, 195, 74, 0.2);
    border: 2px solid #C5E1A5;
    transition: transform 0.2s;
}

.metric-card:hover {
    transform: translateY(-5px);
    box-shadow: 0 5px 15px rgba(139, 195, 74, 0.3);
}

.metric-card h3 {
    color: #33691E;
    font-size: 1rem;
    margin-bottom: 0.5rem;
}

.metric-card .value {
    font-size: 2rem;
    font-weight: bold;
    color: #2E7D32;
    margin: 0.5rem 0;
}

.metric-card .timestamp {
    font-size: 0.9rem;
    color: #558B2F;
}

.charts-container {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(500px, 1fr));
    gap: 20px;
}

.chart-wrapper {
    background: white;
    padding: 1.5rem;
    border-radius: 12px;
    box-shadow: 0 3px 10px rgba(139, 195, 74, 0.2);
}

.chart-wrapper h3 {
    color: #2E7D32;
    margin-bottom: 1rem;
}

.visualization {
    background: white;
    padding: 1.5rem;
    border-radius: 12px;
    box-shadow: 0 3px 10px rgba(139, 195, 74, 0.2);
}

.visualization h3 {
    color: #2E7D32;
    margin-bottom: 1rem;
}

#3d-canvas {
    width: 100%;
    height: 400px;
    border-radius: 8px;
    overflow: hidden;
}

.raw-data {
    background: white;
    padding: 1.5rem;
    border-radius: 12px;
    box-shadow: 0 3px 10px rgba(139, 195, 74, 0.2);
}

.raw-data h3 {
    color: #2E7D32;
    margin-bottom: 1rem;
}

.raw-data pre {
    background: #F1F8E9;
    padding: 1rem;
    border-radius: 8px;
    overflow-x: auto;
    font-size: 0.9rem;
    color: #33691E;
    border: 1px solid #C5E1A5;
}

@media (max-width: 768px) {
    header h1 {
        font-size: 1.8rem;
    }
    
    .charts-container {
        grid-template-columns: 1fr;
    }
}
```

---

### **Option 3: Node-RED Dashboard (Simplest) 🎯**

**Already available in your setup!**

#### **Steps to Make it Public:**

1. **Enable Node-RED Dashboard UI:**

Your Node-RED is already at `http://localhost:1880`. The dashboard is at:
```
http://localhost:1880/ui
```

2. **Add Dashboard Nodes:**

In Node-RED, install dashboard nodes:
```bash
cd /home/hs32/Documents/Projects/adt/simulation
npm install node-red-dashboard
```

3. **Create Public Dashboard Flow:**

Add these nodes in Node-RED:
- **Chart node** → Temperature over time
- **Gauge node** → Humidity, soil moisture
- **Text node** → Device status
- **Worldmap node** → Farm location

4. **Deploy Publicly:**

**Option A - Using ngrok (Quick test):**
```bash
# Install ngrok
snap install ngrok

# Expose Node-RED UI publicly
ngrok http 1880
```

You'll get a public URL like: `https://abc123.ngrok.io/ui`

**Option B - Deploy to Render/Railway:**

Create `Dockerfile` in simulation/:
```dockerfile
FROM nodered/node-red:latest

USER root
RUN npm install node-red-dashboard
USER node-red

COPY flows.json /data/flows.json
COPY settings.js /data/settings.js

EXPOSE 1880
CMD ["node-red"]
```

Deploy to Render.com (same as your API).

---

### **Option 4: Grafana + InfluxDB (Production-Ready)**

For a **professional monitoring solution**.

#### **Architecture:**
```
Node-RED → InfluxDB (time-series DB) → Grafana (visualization)
```

#### **Quick Setup:**

**docker-compose.yml:**
```yaml
version: '3.8'
services:
  influxdb:
    image: influxdb:2.7
    ports:
      - "8086:8086"
    volumes:
      - influx-data:/var/lib/influxdb2
    environment:
      - DOCKER_INFLUXDB_INIT_MODE=setup
      - DOCKER_INFLUXDB_INIT_USERNAME=admin
      - DOCKER_INFLUXDB_INIT_PASSWORD=adminpassword
      - DOCKER_INFLUXDB_INIT_ORG=farm-org
      - DOCKER_INFLUXDB_INIT_BUCKET=telemetry

  grafana:
    image: grafana/grafana:latest
    ports:
      - "3000:3000"
    volumes:
      - grafana-data:/var/lib/grafana
    environment:
      - GF_AUTH_ANONYMOUS_ENABLED=true
      - GF_AUTH_ANONYMOUS_ORG_ROLE=Viewer
      - GF_SECURITY_ALLOW_EMBEDDING=true

volumes:
  influx-data:
  grafana-data:
```

**Node-RED Flow Addition:**
Add **influxdb out** node to write telemetry to InfluxDB.

**Result:** Professional dashboards at `http://localhost:3000` (Grafana)

---

## 🚀 Recommended Deployment Strategy

### **For Quick Demo (Today):**
Use **Option 3 (Node-RED Dashboard + ngrok)**
- ✅ 10 minutes to setup
- ✅ Works immediately
- ✅ No coding required

### **For Production (Long-term):**
Use **Option 2 (Custom React Dashboard)**
- ✅ Professional appearance
- ✅ Fully customizable
- ✅ Deploy to GitHub Pages, Netlify, or Vercel (free)
- ✅ No authentication barriers

### **For Enterprise:**
Use **Option 4 (Grafana)**
- ✅ Industry standard
- ✅ Advanced features
- ✅ Scalable

---

## 📦 Next Steps

Would you like me to:
1. **Create the custom React dashboard** (Option 2) in your project?
2. **Set up Node-RED Dashboard** with public access (Option 3)?
3. **Configure Grafana** for professional monitoring (Option 4)?

Let me know which direction you'd prefer! 🌾
