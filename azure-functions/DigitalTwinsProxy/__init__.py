"""
Azure Function: Digital Twins API Proxy
Provides public access to Azure Digital Twins data for the Explorer
No authentication required - uses Managed Identity internally
"""

import azure.functions as func
import json
import os
import logging
from azure.identity import DefaultAzureCredential
from azure.digitaltwins.core import DigitalTwinsClient

# Initialize Digital Twins client
ADT_URL = os.environ.get("ADT_INSTANCE_URL", "https://farm-digital-twin.api.sea.digitaltwins.azure.net")
credential = DefaultAzureCredential()
dt_client = None

try:
    dt_client = DigitalTwinsClient(ADT_URL, credential)
    logging.info(f"Digital Twins proxy initialized for: {ADT_URL}")
except Exception as e:
    logging.error(f"Failed to initialize Digital Twins client: {str(e)}")


def main(req: func.HttpRequest) -> func.HttpResponse:
    """
    Public proxy endpoint for Digital Twins Explorer
    Supports multiple operations via query parameters
    """
    
    logging.info('DigitalTwinsProxy function triggered')
    
    # CORS headers for all responses
    cors_headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "Content-Type, Authorization",
        "Cache-Control": "no-cache"
    }
    
    # Handle OPTIONS preflight request
    if req.method == "OPTIONS":
        return func.HttpResponse("", status_code=200, headers=cors_headers)
    
    try:
        if not dt_client:
            return func.HttpResponse(
                json.dumps({"error": "Digital Twins client not initialized"}),
                status_code=500,
                mimetype="application/json",
                headers=cors_headers
            )
        
        # Get operation from query parameter or body
        operation = req.params.get('operation') or req.params.get('op')
        
        if not operation:
            # Default: List all twins
            operation = "listTwins"
        
        # Route to appropriate handler
        if operation == "listTwins":
            result = list_twins()
        elif operation == "getTwin":
            twin_id = req.params.get('twinId') or req.params.get('id')
            result = get_twin(twin_id)
        elif operation == "query":
            query_text = req.params.get('query') or req.get_body().decode('utf-8')
            result = query_twins(query_text)
        elif operation == "listModels":
            result = list_models()
        elif operation == "getModel":
            model_id = req.params.get('modelId')
            result = get_model(model_id)
        elif operation == "listRelationships":
            twin_id = req.params.get('twinId')
            result = list_relationships(twin_id)
        else:
            result = {"error": f"Unknown operation: {operation}"}
        
        return func.HttpResponse(
            json.dumps(result, indent=2, default=str),
            status_code=200,
            mimetype="application/json",
            headers=cors_headers
        )
        
    except Exception as e:
        logging.error(f"Error in proxy: {str(e)}")
        return func.HttpResponse(
            json.dumps({
                "error": "Proxy operation failed",
                "message": str(e)
            }),
            status_code=500,
            mimetype="application/json",
            headers=cors_headers
        )


def list_twins():
    """List all digital twins"""
    try:
        query = "SELECT * FROM digitaltwins"
        twins = list(dt_client.query_twins(query))
        return {
            "value": twins,
            "count": len(twins)
        }
    except Exception as e:
        logging.error(f"Error listing twins: {str(e)}")
        return {"error": str(e), "value": []}


def get_twin(twin_id):
    """Get a specific twin by ID"""
    if not twin_id:
        return {"error": "twinId parameter is required"}
    
    try:
        twin = dt_client.get_digital_twin(twin_id)
        return twin
    except Exception as e:
        logging.error(f"Error getting twin {twin_id}: {str(e)}")
        return {"error": str(e)}


def query_twins(query_text):
    """Execute a custom query"""
    if not query_text:
        return {"error": "query parameter is required"}
    
    try:
        results = list(dt_client.query_twins(query_text))
        return {
            "value": results,
            "count": len(results)
        }
    except Exception as e:
        logging.error(f"Error executing query: {str(e)}")
        return {"error": str(e), "value": []}


def list_models():
    """List all models"""
    try:
        models = list(dt_client.list_models())
        return {
            "value": models,
            "count": len(models)
        }
    except Exception as e:
        logging.error(f"Error listing models: {str(e)}")
        return {"error": str(e), "value": []}


def get_model(model_id):
    """Get a specific model"""
    if not model_id:
        return {"error": "modelId parameter is required"}
    
    try:
        model = dt_client.get_model(model_id)
        return model
    except Exception as e:
        logging.error(f"Error getting model: {str(e)}")
        return {"error": str(e)}


def list_relationships(twin_id):
    """List relationships for a twin"""
    if not twin_id:
        return {"error": "twinId parameter is required"}
    
    try:
        relationships = list(dt_client.list_relationships(twin_id))
        return {
            "value": relationships,
            "count": len(relationships)
        }
    except Exception as e:
        logging.error(f"Error listing relationships: {str(e)}")
        return {"error": str(e), "value": []}
