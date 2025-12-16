import logging
import json
import pickle
import numpy as np
import os
from datetime import datetime
import azure.functions as func

# Load model once at cold start
MODEL_PATH = os.getenv("AI_MODEL_PATH", "models/random_forest_v1.pkl")
SCALER_PATH = os.getenv("AI_SCALER_PATH", "models/scaler.pkl")
MODEL_VERSION = "v1.0"

# Global model cache
_model = None
_scaler = None

def load_model():
    """Load the trained Random Forest model"""
    global _model
    if _model is None:
        try:
            model_full_path = os.path.join(os.path.dirname(__file__), '..', MODEL_PATH)
            with open(model_full_path, 'rb') as f:
                _model = pickle.load(f)
            logging.info("Model loaded successfully")
        except FileNotFoundError:
            logging.warning(f"Model file not found at {model_full_path}")
            _model = None
    return _model

def load_scaler():
    """Load the feature scaler"""
    global _scaler
    if _scaler is None:
        try:
            scaler_full_path = os.path.join(os.path.dirname(__file__), '..', SCALER_PATH)
            with open(scaler_full_path, 'rb') as f:
                _scaler = pickle.load(f)
            logging.info("Scaler loaded successfully")
        except FileNotFoundError:
            logging.warning("Scaler file not found, proceeding without scaling")
            _scaler = None
    return _scaler

def simulate_prediction(temperature, humidity, soil_moisture):
    """Simulation-based prediction (fallback when model is unavailable)"""
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
    """Real model inference"""
    features = np.array([[temperature, humidity, soil_moisture]])
    
    if scaler is not None:
        features = scaler.transform(features)
    
    prediction = model.predict(features)[0]
    probabilities = model.predict_proba(features)[0]
    confidence = float(np.max(probabilities))
    
    top_indices = np.argsort(probabilities)[-3:][::-1]
    alternatives = [
        {
            "crop": model.classes_[i],
            "confidence": float(probabilities[i])
        }
        for i in top_indices[1:]
    ]
    
    return prediction, confidence, alternatives

def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Azure Function entry point for AI inference.
    
    Expected request body:
    {
        "temperature": 30.5,
        "humidity": 70,
        "soilMoisture": 45.2
    }
    """
    logging.info('AI Inference function triggered')
    
    start_time = datetime.now()
    
    try:
        # Parse request body
        req_body = req.get_json()
        
        temperature = float(req_body.get('temperature'))
        humidity = float(req_body.get('humidity'))
        soil_moisture = float(req_body.get('soilMoisture'))
        
        # Validate input ranges
        if not (0 <= temperature <= 50):
            return func.HttpResponse(
                json.dumps({"error": "Temperature out of range (0-50)"}),
                status_code=400,
                mimetype="application/json"
            )
        
        if not (0 <= humidity <= 100):
            return func.HttpResponse(
                json.dumps({"error": "Humidity out of range (0-100)"}),
                status_code=400,
                mimetype="application/json"
            )
        
        if not (0 <= soil_moisture <= 100):
            return func.HttpResponse(
                json.dumps({"error": "Soil moisture out of range (0-100)"}),
                status_code=400,
                mimetype="application/json"
            )
        
        # Load model
        model = load_model()
        scaler = load_scaler()
        
        # Perform inference
        if model is not None:
            prediction, confidence, alternatives = predict_with_model(
                model, scaler, temperature, humidity, soil_moisture
            )
            inference_method = "model"
        else:
            prediction, confidence, alternatives = simulate_prediction(
                temperature, humidity, soil_moisture
            )
            inference_method = "simulation"
        
        # Calculate inference time
        end_time = datetime.now()
        inference_time_ms = int((end_time - start_time).total_seconds() * 1000)
        
        # Prepare response
        result = {
            "crop": prediction,
            "confidence": confidence,
            "alternatives": alternatives,
            "inferenceTime": inference_time_ms,
            "inferenceLocation": "cloud",
            "inferenceMethod": inference_method,
            "modelVersion": MODEL_VERSION,
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "input": {
                "temperature": temperature,
                "humidity": humidity,
                "soilMoisture": soil_moisture
            }
        }
        
        logging.info(f"Inference completed: {prediction} ({confidence:.2f})")
        
        return func.HttpResponse(
            json.dumps(result),
            status_code=200,
            mimetype="application/json"
        )
        
    except ValueError as e:
        logging.error(f"ValueError: {str(e)}")
        return func.HttpResponse(
            json.dumps({
                "error": str(e),
                "errorType": "ValueError"
            }),
            status_code=400,
            mimetype="application/json"
        )
    
    except Exception as e:
        logging.error(f"Error: {str(e)}")
        return func.HttpResponse(
            json.dumps({
                "error": str(e),
                "errorType": type(e).__name__
            }),
            status_code=500,
            mimetype="application/json"
        )
