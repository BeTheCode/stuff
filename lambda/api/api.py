import json
import boto3
import os
from datetime import datetime, timedelta
from boto3.dynamodb.conditions import Key

dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])

def handler(event, context):
    """Handle API requests"""
    try:
        http_method = event['httpMethod']
        path = event.get('path', '/')
        query_params = event.get('queryStringParameters', {})
        
        routes = {
            'GET': {
                '/devices': get_devices,
                '/alerts': get_alerts,
                '/analysis': get_analysis,
                '/metrics': get_metrics
            }
        }
        
        # Route the request
        if http_method in routes and path in routes[http_method]:
            response = routes[http_method][path](query_params)
        else:
            response = {
                'statusCode': 404,
                'body': json.dumps('Not Found')
            }
        
        # Add CORS headers
        response['headers'] = {
            'Access-Control-Allow-Origin': '*',
            'Access-Control-Allow-Methods': 'GET,POST,OPTIONS',
            'Access-Control-Allow-Headers': 'Content-Type'
        }
        
        return response
    except Exception as e:
        return {
            'statusCode': 500,
            'body': json.dumps({'error': str(e)})
        }

def get_devices(params):
    """Get device list and status"""
    response = table.query(
        IndexName='device-index',
        KeyConditionExpression=Key('type').eq('device')
    )
    
    return {
        'statusCode': 200,
        'body': json.dumps(response['Items'])
    }
