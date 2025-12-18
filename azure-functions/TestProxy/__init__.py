"""
Test function to verify Azure Function is working
"""

import azure.functions as func
import json
import logging

def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Test function triggered')
    
    cors_headers = {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Methods": "GET, POST, OPTIONS",
        "Access-Control-Allow-Headers": "*",
    }
    
    if req.method == "OPTIONS":
        return func.HttpResponse("", status_code=200, headers=cors_headers)
    
    return func.HttpResponse(
        json.dumps({
            "status": "Function is working!",
            "method": req.method,
            "url": req.url
        }),
        status_code=200,
        mimetype="application/json",
        headers=cors_headers
    )
