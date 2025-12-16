import sys
import json
import pickle
import numpy as np
import os
from datetime import datetime

# Configuration
MODEL_PATH = os.getenv("AI_MODEL_PATH", "/home/pi/agriculture-ai/models/random_forest_v1.pkl")
SCALER_PATH = os.getenv("AI_SCALER_PATH", "/home/pi/agriculture-ai/models/scaler.pkl")
MODEL_VERSION = "v1.0"

def load_model():
    """Load the trained Random Forest model"""
    try:
        with open(MODEL_PATH, 'rb') as f:
            model = pickle.load(f)
        return model
    except FileNotFoundError:
        return None

def load_scaler():
    """Load the feature scaler if available"""
    try:
        with open(SCALER_PATH, 'rb') as f:
            scaler = pickle.load(f)
        return scaler
    except FileNotFoundError:
        return None

def simulate_prediction(temperature, humidity, soil_moisture):
    """
    Simulation-based prediction logic.
    Replace this with actual model inference when model file is available.
    Based on research manuscript metrics.
    """
    # Decision logic based on agricultural domain knowledge
    if temperature > 30 and soil_moisture > 60 and humidity > 70:
        prediction = "Rice"
        confidence = 0.96
        alternatives = [
            {"crop": "Sugarcane", "confidence": 0.82},
            {"crop": "Jute", "confidence": 0.68}
        ]
    elif temperature > 25 and temperature <= 30 and soil_moisture > 50:
        prediction = "Maize"
        confidence = 0.88
        alternatives = [
            {"crop": "Rice", "confidence": 0.75},
            {"crop": "Cotton", "confidence": 0.62}
        ]
    elif temperature < 20 and soil_moisture < 40:
        prediction = "Wheat"
        confidence = 0.92
        alternatives = [
            {"crop": "Barley", "confidence": 0.79},
            {"crop": "Chickpea", "confidence": 0.71}
        ]
    elif soil_moisture < 30:
        prediction = "Millet"
        confidence = 0.85
        alternatives = [
            {"crop": "Sorghum", "confidence": 0.77},
            {"crop": "Groundnut", "confidence": 0.64}
        ]
    else:
        prediction = "Vegetables"
        confidence = 0.78
        alternatives = [
            {"crop": "Maize", "confidence": 0.72},
            {"crop": "Pulses", "confidence": 0.65}
        ]
    
    return prediction, confidence, alternatives

def predict_with_model(model, scaler, temperature, humidity, soil_moisture):
    """
    Real model inference using trained Random Forest.
    """
    # Prepare features
    features = np.array([[temperature, humidity, soil_moisture]])
    
    # Apply scaling if scaler is available
    if scaler is not None:
        features = scaler.transform(features)
    
    # Get prediction
    prediction = model.predict(features)[0]
    
    # Get confidence scores
    probabilities = model.predict_proba(features)[0]
    confidence = np.max(probabilities)
    
    # Get top 3 alternatives
    top_indices = np.argsort(probabilities)[-3:][::-1]
    alternatives = [
        {
            "crop": model.classes_[i],
            "confidence": float(probabilities[i])
        }
        for i in top_indices[1:]  # Skip the top prediction
    ]
    
    return prediction, float(confidence), alternatives

def predict(temperature, humidity, soil_moisture):
    """
    Main prediction function.
    Tries to use real model, falls back to simulation if unavailable.
    """
    start_time = datetime.now()
    
    # Try loading real model
    model = load_model()
    scaler = load_scaler()
    
    if model is not None:
        # Use real model
        prediction, confidence, alternatives = predict_with_model(
            model, scaler, temperature, humidity, soil_moisture
        )
        inference_method = "model"
    else:
        # Fall back to simulation
        prediction, confidence, alternatives = simulate_prediction(
            temperature, humidity, soil_moisture
        )
        inference_method = "simulation"
    
    # Calculate inference time
    end_time = datetime.now()
    inference_time_ms = int((end_time - start_time).total_seconds() * 1000)
    
    # Prepare result
    result = {
        "crop": prediction,
        "confidence": confidence,
        "alternatives": alternatives,
        "inferenceTime": inference_time_ms,
        "inferenceLocation": "edge",
        "inferenceMethod": inference_method,
        "modelVersion": MODEL_VERSION,
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "input": {
            "temperature": temperature,
            "humidity": humidity,
            "soilMoisture": soil_moisture
        }
    }
    
    return result

def main():
    """
    Main entry point for command-line execution.
    Reads arguments from command line and outputs JSON result.
    """
    try:
        # Validate arguments
        if len(sys.argv) < 4:
            raise ValueError("Usage: python3 predict_crop.py <temperature> <humidity> <soil_moisture>")
        
        # Parse input
        temperature = float(sys.argv[1])
        humidity = float(sys.argv[2])
        soil_moisture = float(sys.argv[3])
        
        # Validate ranges
        if not (0 <= temperature <= 50):
            raise ValueError(f"Temperature out of range: {temperature}")
        if not (0 <= humidity <= 100):
            raise ValueError(f"Humidity out of range: {humidity}")
        if not (0 <= soil_moisture <= 100):
            raise ValueError(f"Soil moisture out of range: {soil_moisture}")
        
        # Get prediction
        result = predict(temperature, humidity, soil_moisture)
        
        # Output as JSON
        print(json.dumps(result))
        sys.exit(0)
        
    except ValueError as e:
        error_result = {
            "error": str(e),
            "errorType": "ValueError",
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        print(json.dumps(error_result))
        sys.exit(1)
        
    except Exception as e:
        error_result = {
            "error": str(e),
            "errorType": type(e).__name__,
            "timestamp": datetime.utcnow().isoformat() + "Z"
        }
        print(json.dumps(error_result))
        sys.exit(1)

if __name__ == "__main__":
    main()
