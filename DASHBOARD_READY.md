# 🎉 Prediction Dashboard - Quick Start Guide

## ✅ **Status: FULLY OPERATIONAL**

Both services are now running successfully!

---

## 🌐 **Access URLs**

### **Prediction Dashboard**
- **Local**: http://localhost:8501
- **Network**: http://10.5.0.2:8501  
- **External**: http://45.95.161.18:8501

### **Simulation API**
- **Endpoint**: http://localhost:1880/api/telemetry
- **Node-RED UI**: http://localhost:1880

---

## 📊 **What You'll See**

### **Dashboard Features**

1. **Live Sensor Data** (top of page)
   - 🌡️ Temperature
   - 💧 Humidity
   - 🌱 Soil Moisture
   - ⏰ Last Update Time

2. **Crop Yield Predictions** (3 models)
   - Standard Random Forest
   - Cascade Random Forest
   - Hierarchical Random Forest
   - Each shows predicted crop name/class

3. **Interactive Charts**
   - Model comparison bar chart
   - Temperature gauge with zones
   - Feature importance ranking

4. **Configuration (Sidebar)**
   - API endpoint URL
   - Auto-refresh toggle
   - Refresh interval slider
   - Manual input fields for farm parameters

---

## 🎮 **How to Use**

### **Basic Usage**
1. Open http://localhost:8501 in your browser
2. Check "🔄 Auto Refresh" in the sidebar (enabled by default)
3. Watch real-time predictions update every 5 seconds
4. Adjust refresh rate with the slider (1-60 seconds)

### **Customize Predictions**
Use the sidebar inputs to configure farm parameters:
- **Area**: Farm size in hectares
- **District & Season**: Location and timing
- **Weather**: Max/Min temp, humidity, rainfall
- **Soil**: pH level, moisture
- **Crop Growth**: Transplant, growth, harvest days

### **View Detailed Analysis**
- Scroll down to see comparison charts
- Check feature importance to understand what drives predictions
- Expand "View Raw Data" to see JSON and processed features

---

## 🔧 **Management Commands**

### **Restart Dashboard**
```bash
pkill -f streamlit
streamlit run prediction/app/app.py --server.port 8501 --server.headless true &
```

### **Restart Simulation**
```bash
cd /home/hs32/Documents/Projects/adt/simulation
pkill -f node-red
./node_modules/.bin/node-red --userDir . > ../node-red.log 2>&1 &
```

### **Check Status**
```bash
# Test simulation API
curl http://localhost:1880/api/telemetry

# Check if services are running
ps aux | grep streamlit
ps aux | grep node-red
```

### **View Logs**
```bash
# Streamlit logs
tail -f /home/hs32/Documents/Projects/adt/streamlit.log

# Node-RED logs
tail -f /home/hs32/Documents/Projects/adt/node-red.log
```

---

## 🔄 **Retrain Models** (if needed)

If you need to retrain models with new data or after library updates:

```bash
cd /home/hs32/Documents/Projects/adt
python prediction/retrain_models.py
```

Then restart the dashboard.

---

## 📁 **Project Structure**

```
/home/hs32/Documents/Projects/adt/
├── simulation/
│   ├── flows.json              # Node-RED flow (with API endpoint)
│   └── node_modules/           # Node-RED installation
├── prediction/
│   ├── app/
│   │   ├── app.py              # Main Streamlit application
│   │   └── requirements.txt    # Python dependencies
│   ├── output/
│   │   ├── *.joblib            # Trained models (compatible)
│   │   ├── model_config.joblib # Feature configuration
│   │   ├── label_encoders.joblib # Categorical encoders
│   │   └── scaler.joblib       # Feature scaler
│   └── retrain_models.py       # Model retraining script
├── streamlit.log               # Dashboard logs
└── node-red.log                # Simulation logs
```

---

## 🎯 **Key Features Implemented**

✅ **Real-time Data Flow**
- Node-RED simulation → API endpoint → Streamlit dashboard

✅ **Machine Learning**
- 3 different Random Forest variants
- Feature engineering and scaling
- Categorical encoding

✅ **Visualizations**
- Live sensor metrics
- Model comparison charts
- Temperature gauges
- Feature importance plots

✅ **User Controls**
- Configurable API endpoint
- Adjustable refresh rate
- Manual parameter inputs
- Auto-refresh toggle

---

## 💡 **Tips**

- **Slow Updates?** Increase refresh interval to reduce load
- **Different Data Source?** Change API endpoint in sidebar
- **Custom Analysis?** Edit `/prediction/app/app.py` to add new charts
- **Model Issues?** Run `retrain_models.py` to rebuild with current libraries

---

## 🎊 **Success!**

Your prediction dashboard is fully operational! 🚀

**Next Steps:**
1. Open the dashboard in your browser
2. Watch live predictions update
3. Experiment with different parameters
4. Enjoy real-time crop yield predictions!

---

**Need Help?**
- Check logs: `tail -f streamlit.log` or `tail -f node-red.log`
- Test API: `curl http://localhost:1880/api/telemetry`
- Restart services using commands above
