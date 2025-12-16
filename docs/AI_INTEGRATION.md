# AI Model Integration - Flexible Architecture

## Overview
This document describes the flexible AI model deployment strategy that allows running inference either:
- **On the Edge** (Raspberry Pi)
- **In the Cloud** (Azure Functions)

## Architecture Decision

### Edge Computing (Raspberry Pi)
**Pros**:
- Low latency (~10-50ms)
- Works offline
- Reduced cloud costs
- Privacy (data stays local)

**Cons**:
- Limited compute resources
- Manual model updates
- Device-specific deployment

### Cloud Computing (Azure Functions)
**Pros**:
- Centralized model management
- Easy A/B testing
- Scalable across fleet
- Advanced logging/monitoring

**Cons**:
- Network latency (~100-300ms)
- Requires internet connection
- Data transfer costs

## Implementation Strategy

### Unified Data Format
Both edge and cloud will receive the same input format:
```json
{
  "temperature": 30.5,
  "humidity": 70,
  "soilMoisture": 45.2,
  "location": "zone_A",
  "timestamp": "2025-12-14T21:39:15.000Z"
}
```

Both will return:
```json
{
  "crop": "Rice",
  "confidence": 0.96,
  "alternatives": [
    {"crop": "Maize", "confidence": 0.78},
    {"crop": "Wheat", "confidence": 0.45}
  ],
  "inferenceTime": 45,
  "inferenceLocation": "edge|cloud",
  "modelVersion": "v1.0"
}
```

### Routing Logic
Node-RED will have a configuration node that decides where to route:
```javascript
const AI_MODE = env.get("AI_MODE"); // "edge", "cloud", or "auto"

if (AI_MODE === "edge") {
  // Route to local Python script
} else if (AI_MODE === "cloud") {
  // Route to Azure Function
} else {
  // Auto-select based on connectivity/latency
}
```

## Edge Implementation

### 1. Model File Structure
```
/home/pi/agriculture-ai/
├── models/
│   ├── random_forest_v1.pkl
│   ├── scaler.pkl
│   └── model_metadata.json
├── predict_crop.py
└── requirements.txt
```

### 2. Inference Script (predict_crop.py)
See: `simulation/ai-edge/predict_crop.py`

### 3. Node-RED Integration
- **exec node**: Calls Python script
- **Function node**: Prepares arguments and parses response

## Cloud Implementation

### 1. Azure Function Structure
```
azure-functions/
├── AI_Inference/
│   ├── __init__.py
│   ├── function.json
│   └── requirements.txt
├── models/
│   └── random_forest_v1.pkl
└── host.json
```

### 2. Function Endpoint
- **URL**: `https://<function-app>.azurewebsites.net/api/predict`
- **Method**: POST
- **Authentication**: Function key or Azure AD

### 3. Node-RED Integration
- **HTTP Request node**: POST to Function URL
- **Function node**: Parse response

## Configuration

### Environment Variables
Add to `.env`:
```bash
# AI Configuration
AI_MODE=cloud              # Options: edge, cloud, auto
AI_CLOUD_ENDPOINT=https://your-function-app.azurewebsites.net/api/predict
AI_CLOUD_KEY=your-function-key
AI_EDGE_SCRIPT=/home/pi/agriculture-ai/predict_crop.py
AI_TIMEOUT=5000           # Milliseconds
```

## Testing Strategy

### Edge Testing
```bash
python3 predict_crop.py 30.5 70 45.2
# Expected: {"crop": "Rice", "confidence": 0.96, ...}
```

### Cloud Testing
```bash
curl -X POST https://your-function.azurewebsites.net/api/predict \
  -H "Content-Type: application/json" \
  -d '{"temperature": 30.5, "humidity": 70, "soilMoisture": 45.2}'
```

## Monitoring & Fallback

### Metrics to Track
- Inference latency
- Success rate
- Model version
- Inference location distribution

### Fallback Strategy
```javascript
// In Node-RED function node
let result = null;

try {
  if (AI_MODE === "cloud") {
    result = await callCloudAPI(data);
  }
} catch (error) {
  node.warn("Cloud inference failed, falling back to edge");
  result = callEdgeInference(data);
}

if (!result) {
  // Ultimate fallback: Rule-based logic
  result = ruleBasedPrediction(data);
}
```

## Migration Path

### Phase 4A: Edge-First (Current)
1. Deploy model to Raspberry Pi
2. Test locally
3. Integrate with Node-RED
4. Deploy to production

### Phase 4B: Cloud-First (Next)
1. Create Azure Function
2. Deploy model to Function
3. Add HTTP endpoint to Node-RED
4. A/B test edge vs cloud

### Phase 4C: Hybrid (Final)
1. Implement routing logic
2. Add health checks
3. Enable auto-fallback
4. Monitor performance metrics
