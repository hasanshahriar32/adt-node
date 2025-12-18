import azure.functions as func
import json
import os
import logging

# Global variables - will be initialized on first request
ADT_URL = os.environ.get("ADT_INSTANCE_URL", "https://farm-digital-twin.api.sea.digitaltwins.azure.net")
_credential = None
_dt_client = None

def get_dt_client():
    """Lazy initialization of Digital Twins client"""
    global _credential, _dt_client
    
    if _dt_client is None:
        try:
            from azure.identity import DefaultAzureCredential
            from azure.digitaltwins.core import DigitalTwinsClient
            
            logging.info(f"Initializing DT client for: {ADT_URL}")
            _credential = DefaultAzureCredential()
            _dt_client = DigitalTwinsClient(ADT_URL, _credential)
            logging.info("DT client initialized successfully")
        except Exception as e:
            logging.error(f"Failed to initialize DT client: {e}", exc_info=True)
            raise
    
    return _dt_client

def main(req: func.HttpRequest) -> func.HttpResponse:
    cors_headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "*"
    }
    
    if req.method == "OPTIONS":
        return func.HttpResponse("", status_code=200, headers=cors_headers)
    
    try:
        logging.info(f"Request: {req.method} {req.url}")
        route = req.route_params.get('route', '')
        logging.info(f"Route: {route}")
        
        # Get client (lazy initialization)
        try:
            dt_client = get_dt_client()
        except Exception as init_err:
            logging.error(f"Client initialization failed: {init_err}")
            return func.HttpResponse(
                json.dumps({"error": "Failed to initialize Digital Twins client", "message": str(init_err)}),
                status_code=503,
                mimetype="application/json",
                headers=cors_headers
            )
        
        # Handle models endpoint
        if 'models' in route.lower():
            logging.info("Listing models")
            # Get query parameters
            include_definition = req.params.get('includeModelDefinition', 'false').lower() == 'true'
            
            models = list(dt_client.list_models(include_model_definition=include_definition))
            logging.info(f"Found {len(models)} models")
            return func.HttpResponse(
                json.dumps({"value": models}, default=str),
                status_code=200,
                mimetype="application/json",
                headers=cors_headers
            )
        
        # Handle query endpoint
        elif 'query' in route.lower():
            try:
                body = json.loads(req.get_body())
                query_text = body.get('query', 'SELECT * FROM digitaltwins')
                logging.info(f"Query: {query_text}")
            except Exception as body_err:
                logging.warning(f"Body parse error: {body_err}")
                query_text = 'SELECT * FROM digitaltwins'
            
            results = list(dt_client.query_twins(query_text))
            logging.info(f"Query returned {len(results)} results")
            return func.HttpResponse(
                json.dumps({"value": results}, default=str),
                status_code=200,
                mimetype="application/json",
                headers=cors_headers
            )
        
        # Handle individual twin or list digitaltwins
        elif 'digitaltwins' in route.lower():
            # Check if requesting a specific twin
            parts = [p for p in route.split('/') if p]
            twin_id = None
            
            # Look for pattern: digitaltwins/{twinId}
            for i, part in enumerate(parts):
                if part.lower() == 'digitaltwins' and i + 1 < len(parts):
                    next_part = parts[i + 1]
                    if next_part.lower() not in ['relationships', 'incomingrelationships']:
                        twin_id = next_part
                        break
            
            if twin_id:
                # Get specific twin
                logging.info(f"Getting twin: {twin_id}")
                try:
                    twin = dt_client.get_digital_twin(twin_id)
                    logging.info(f"Found twin: {twin_id}")
                    return func.HttpResponse(
                        json.dumps(twin, default=str),
                        status_code=200,
                        mimetype="application/json",
                        headers=cors_headers
                    )
                except Exception as twin_err:
                    logging.error(f"Twin not found: {twin_id} - {twin_err}")
                    return func.HttpResponse(
                        json.dumps({"error": f"Twin not found: {twin_id}"}),
                        status_code=404,
                        mimetype="application/json",
                        headers=cors_headers
                    )
            else:
                # List all twins
                logging.info("Listing all digital twins")
                results = list(dt_client.query_twins('SELECT * FROM digitaltwins'))
                logging.info(f"Found {len(results)} twins")
                return func.HttpResponse(
                    json.dumps({"value": results}, default=str),
                    status_code=200,
                    mimetype="application/json",
                    headers=cors_headers
                )
        
        # Handle relationships endpoint
        elif 'relationships' in route.lower():
            # Extract twin ID from route
            parts = route.split('/')
            twin_id = None
            for i, part in enumerate(parts):
                if part == 'digitaltwins' and i + 1 < len(parts):
                    twin_id = parts[i + 1]
                    break
            
            if twin_id and twin_id != 'relationships':
                logging.info(f"Listing relationships for twin: {twin_id}")
                relationships = list(dt_client.list_relationships(twin_id))
                logging.info(f"Found {len(relationships)} relationships")
                return func.HttpResponse(
                    json.dumps({"value": relationships}, default=str),
                    status_code=200,
                    mimetype="application/json",
                    headers=cors_headers
                )
            else:
                return func.HttpResponse(
                    json.dumps({"error": "Twin ID required for relationships"}),
                    status_code=400,
                    mimetype="application/json",
                    headers=cors_headers
                )
        
        else:
            logging.warning(f"Unsupported endpoint: {route}")
            return func.HttpResponse(
                json.dumps({"error": "Unsupported endpoint", "route": route}),
                status_code=404,
                mimetype="application/json",
                headers=cors_headers
            )
            
    except Exception as e:
        logging.error(f"Error: {e}", exc_info=True)
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            status_code=500,
            mimetype="application/json",
            headers=cors_headers
        )
