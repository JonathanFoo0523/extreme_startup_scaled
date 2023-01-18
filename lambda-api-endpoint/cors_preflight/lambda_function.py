import json

def lambda_handler(event, context):
    return {
        "statusCode": 200, 
        "body": "hello from me", 
        "headers": {
            "Access-Control-Allow-Credentials": True,
            "Access-Control-Allow-Headers": "Access-Control-Allow-Headers, Origin,Accept, X-Requested-With, Content-Type, Access-Control-Request-Method, Access-Control-Request-Headers",
            "Access-Control-Allow-Origin": "http://127.0.0.1:5000, https://d1zlib8d3siide.cloudfront.net",
            "Access-Control-Allow-Methods": "POST, PUT, GET, OPTIONS",
        }
     }
