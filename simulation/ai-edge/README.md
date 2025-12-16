# Edge AI Setup Guide

## Prerequisites
- Raspberry Pi 3B+ or higher
- Python 3.7+
- Internet connection (for initial setup)

## Installation Steps

### 1. System Update
```bash
sudo apt-get update
sudo apt-get upgrade -y
```

### 2. Install Python Dependencies
```bash
sudo apt-get install python3-pip python3-dev -y
```

### 3. Install ML Libraries
```bash
# Create virtual environment (recommended)
python3 -m venv /home/pi/agriculture-ai/venv
source /home/pi/agriculture-ai/venv/bin/activate

# Install required packages
pip3 install -r requirements.txt
```

### 4. Setup Directory Structure
```bash
mkdir -p /home/pi/agriculture-ai/models
cd /home/pi/agriculture-ai
```

### 5. Copy Files
Copy the following files to `/home/pi/agriculture-ai/`:
- `predict_crop.py`
- `requirements.txt`

### 6. Test the Script
```bash
# Using virtual environment
source /home/pi/agriculture-ai/venv/bin/activate
python3 predict_crop.py 30.5 70 45.2

# Expected output:
# {"crop": "Rice", "confidence": 0.96, ...}
```

### 7. Set Environment Variables (Optional)
Add to `/home/pi/.bashrc`:
```bash
export AI_MODEL_PATH="/home/pi/agriculture-ai/models/random_forest_v1.pkl"
export AI_SCALER_PATH="/home/pi/agriculture-ai/models/scaler.pkl"
```

## Deploying Your Trained Model

### 1. Export Model from Training Environment
```python
import pickle

# After training your Random Forest model
with open('random_forest_v1.pkl', 'wb') as f:
    pickle.dump(model, f)

# Also save the scaler if you used feature scaling
with open('scaler.pkl', 'wb') as f:
    pickle.dump(scaler, f)
```

### 2. Transfer to Raspberry Pi
```bash
# From your development machine
scp random_forest_v1.pkl pi@<raspberry-pi-ip>:/home/pi/agriculture-ai/models/
scp scaler.pkl pi@<raspberry-pi-ip>:/home/pi/agriculture-ai/models/
```

### 3. Verify Model Loading
```bash
python3 -c "import pickle; model = pickle.load(open('/home/pi/agriculture-ai/models/random_forest_v1.pkl', 'rb')); print('Model loaded successfully')"
```

## Integration with Node-RED

The Python script is called from Node-RED using the `exec` node. No additional configuration needed on the Pi side.

## Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'sklearn'"
```bash
pip3 install scikit-learn
```

### Issue: "Permission denied"
```bash
chmod +x /home/pi/agriculture-ai/predict_crop.py
```

### Issue: Low memory on Raspberry Pi
Consider using a lightweight model:
```python
# During training, limit tree depth
from sklearn.ensemble import RandomForestClassifier
model = RandomForestClassifier(n_estimators=50, max_depth=10)
```

## Performance Benchmarks (Expected)

| Device | Inference Time | Memory Usage |
|--------|----------------|--------------|
| Raspberry Pi 4 | 20-50ms | ~100MB |
| Raspberry Pi 3B+ | 50-100ms | ~100MB |
| Raspberry Pi Zero | 200-500ms | ~80MB |

## Maintenance

### Update Model
```bash
# Backup old model
cp /home/pi/agriculture-ai/models/random_forest_v1.pkl \
   /home/pi/agriculture-ai/models/random_forest_v1_backup.pkl

# Copy new model
scp new_model.pkl pi@<raspberry-pi-ip>:/home/pi/agriculture-ai/models/random_forest_v1.pkl
```

### Monitor Logs
Node-RED will capture stdout/stderr from the Python script automatically in the debug panel.
