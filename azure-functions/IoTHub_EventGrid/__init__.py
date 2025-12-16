"""
Azure Function: IoT Hub Event Grid Trigger
Routes telemetry from IoT Hub to Azure Digital Twins
"""

import logging
import json
import os
from azure.identity import DefaultAzureCredential
from azure.digitaltwins.core import DigitalTwinsClient

# Initialize Digital Twins client (singleton)
ADT_URL = os.environ.get("ADT_INSTANCE_URL")
credential = DefaultAzureCredential()
dt_client = None

if ADT_URL:
    dt_client = DigitalTwinsClient(ADT_URL, credential)
    logging.info(f"Digital Twins client initialized for: {ADT_URL}")


def main(event: dict) -> None:
    """
    Process IoT Hub telemetry event and update Digital Twin
    
    Event Grid Schema:
    {
        "data": {
            "body": {
                "temperature": 28.5,
                "humidity": 75.0,
                "soilMoisture": 65.0,
                "timestamp": "2025-12-16T10:30:00Z"
            },
            "properties": {},
            "systemProperties": {
                "iothub-connection-device-id": "pc_sim_01"
            }
        },
        "eventType": "Microsoft.Devices.DeviceTelemetry",
        "subject": "devices/pc_sim_01",
        "eventTime": "2025-12-16T10:30:00Z",
        "id": "...",
        "dataVersion": "1"
    }
    """
    
    logging.info('IoT Hub Event Grid trigger function started')
    
    try:
        # Parse event
        event_data = event.get('data', {})
        body = event_data.get('body', {})
        system_properties = event_data.get('systemProperties', {})
        
        device_id = system_properties.get('iothub-connection-device-id')
        event_type = event.get('eventType')
        
        logging.info(f"Event Type: {event_type}")
        logging.info(f"Device ID: {device_id}")
        logging.info(f"Telemetry: {json.dumps(body)}")
        
        if not device_id:
            logging.error("No device ID found in event")
            return
        
        if not dt_client:
            logging.error("Digital Twins client not initialized")
            return
        
        # Extract telemetry values
        temperature = body.get('temperature')
        humidity = body.get('humidity')
        soil_moisture = body.get('soilMoisture')
        timestamp = body.get('timestamp') or event.get('eventTime')
        
        # Get twin IDs from environment (can be made dynamic based on device mapping)
        device_twin_id = os.environ.get('DEVICE_TWIN_ID', 'pc_sim_01')
        zone_twin_id = os.environ.get('ZONE_TWIN_ID', 'zone_A')
        
        # Update Device twin telemetry and properties
        device_updates = []
        
        if temperature is not None:
            device_updates.append({
                "op": "replace",
                "path": "/temperature",
                "value": temperature
            })
        
        if humidity is not None:
            device_updates.append({
                "op": "replace",
                "path": "/humidity",
                "value": humidity
            })
        
        if soil_moisture is not None:
            device_updates.append({
                "op": "replace",
                "path": "/soilMoisture",
                "value": soil_moisture
            })
        
        if timestamp:
            device_updates.append({
                "op": "replace",
                "path": "/lastSeen",
                "value": timestamp
            })
            device_updates.append({
                "op": "replace",
                "path": "/status",
                "value": "active"
            })
        
        if device_updates:
            logging.info(f"Updating Device twin: {device_twin_id}")
            dt_client.update_digital_twin(device_twin_id, device_updates)
            logging.info(f"✅ Device twin updated successfully")
        
        # Update Zone twin telemetry
        zone_updates = []
        
        if temperature is not None:
            zone_updates.append({
                "op": "replace",
                "path": "/temperature",
                "value": temperature
            })
        
        if humidity is not None:
            zone_updates.append({
                "op": "replace",
                "path": "/humidity",
                "value": humidity
            })
        
        if soil_moisture is not None:
            zone_updates.append({
                "op": "replace",
                "path": "/soilMoisture",
                "value": soil_moisture
            })
        
        if timestamp:
            zone_updates.append({
                "op": "replace",
                "path": "/lastUpdated",
                "value": timestamp
            })
        
        # Check if AI recommendation is present
        recommended_crop = body.get('recommendedCrop')
        recommendation_confidence = body.get('recommendationConfidence')
        
        if recommended_crop:
            zone_updates.append({
                "op": "replace",
                "path": "/recommendedCrop",
                "value": recommended_crop
            })
            logging.info(f"AI Recommendation: {recommended_crop}")
        
        if recommendation_confidence is not None:
            zone_updates.append({
                "op": "replace",
                "path": "/recommendationConfidence",
                "value": recommendation_confidence
            })
        
        if zone_updates:
            logging.info(f"Updating Zone twin: {zone_twin_id}")
            dt_client.update_digital_twin(zone_twin_id, zone_updates)
            logging.info(f"✅ Zone twin updated successfully")
        
        logging.info("IoT Hub Event Grid trigger function completed successfully")
        
    except Exception as e:
        logging.error(f"Error processing event: {str(e)}")
        logging.exception(e)
        raise
