import azure.functions as func
import json
import os
import logging
from azure.identity import DefaultAzureCredential
from azure.digitaltwins.core import DigitalTwinsClient

# Initialize Digital Twins client (singleton)
ADT_URL = os.environ.get("ADT_INSTANCE_URL")
credential = DefaultAzureCredential()
dt_client = None

if ADT_URL:
    dt_client = DigitalTwinsClient(ADT_URL, credential)
    logging.info(f"Digital Twins client initialized for: {ADT_URL}")


def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Public API endpoint to get current digital twin data
    No authentication required - suitable for public dashboards
    """
    
    logging.info('GetTwinData function triggered')
    
    try:
        if not dt_client:
            return func.HttpResponse(
                json.dumps({"error": "Digital Twins client not initialized"}),
                status_code=500,
                mimetype="application/json"
            )
        
        # Get zone_A twin (contains sensor data)
        zone_twin = dt_client.get_digital_twin("zone_A")
        
        # Get device twin (for status)
        device_twin = dt_client.get_digital_twin("pc_sim_01")
        
        # Get farm twin (for context)
        farm_twin = dt_client.get_digital_twin("farm_001")
        
        # Extract data
        response_data = {
            "farm": {
                "name": farm_twin.get("name", "Unknown"),
                "location": farm_twin.get("location", "Unknown"),
                "totalArea": farm_twin.get("totalArea", 0)
            },
            "zone": {
                "name": zone_twin.get("name", "Unknown"),
                "area": zone_twin.get("area", 0),
                "soilType": zone_twin.get("soilType", "Unknown"),
                "currentCrop": zone_twin.get("currentCrop", "None"),
                "recommendedCrop": zone_twin.get("recommendedCrop", "N/A"),
                "recommendationConfidence": zone_twin.get("recommendationConfidence", 0)
            },
            "sensors": {
                "temperature": zone_twin.get("temperature", 0),
                "humidity": zone_twin.get("humidity", 0),
                "soilMoisture": zone_twin.get("soilMoisture", 0)
            },
            "device": {
                "deviceId": device_twin.get("deviceId", "Unknown"),
                "status": device_twin.get("status", "unknown"),
                "lastSeen": device_twin.get("lastSeen", "Never")
            },
            "metadata": {
                "lastUpdated": zone_twin.get("$metadata", {}).get("$lastUpdateTime", "Unknown"),
                "twinId": zone_twin.get("$dtId"),
                "model": zone_twin.get("$metadata", {}).get("$model")
            }
        }
        
        logging.info(f"Successfully retrieved twin data for zone_A")
        
        return func.HttpResponse(
            json.dumps(response_data, indent=2),
            status_code=200,
            mimetype="application/json",
            headers={
                "Access-Control-Allow-Origin": "*",  # Enable CORS for public access
                "Access-Control-Allow-Methods": "GET, OPTIONS",
                "Access-Control-Allow-Headers": "Content-Type",
                "Cache-Control": "no-cache"  # Prevent caching for real-time data
            }
        )
        
    except Exception as e:
        logging.error(f"Error retrieving twin data: {str(e)}")
        return func.HttpResponse(
            json.dumps({
                "error": "Failed to retrieve twin data",
                "message": str(e)
            }),
            status_code=500,
            mimetype="application/json",
            headers={"Access-Control-Allow-Origin": "*"}
        )
