import json
import boto3
import os
import numpy as np
from datetime import datetime

sagemaker = boto3.client('sagemaker-runtime')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])

def handler(event, context):
    """Process data using ML models"""
    try:
        records = event['Records']
        
        for record in records:
            # Get data
            data = json.loads(record['body'])
            
            # Get predictions
            predictions = get_predictions(data)
            
            # Process results
            process_predictions(predictions, data)
            
            # Store results
            store_results(predictions, data)
        
        return {
            'statusCode': 200,
            'body': json.dumps('ML processing completed')
        }
    except Exception as e:
        print(f"Error in ML processing: {str(e)}")
        raise

def get_predictions(data):
    """Get predictions from SageMaker endpoint"""
    endpoint_name = os.environ['SAGEMAKER_ENDPOINT']
    
    # Prepare data for model
    payload = prepare_payload(data)
    
    # Get prediction
    response = sagemaker.invoke_endpoint(
        EndpointName=endpoint_name,
        ContentType='application/json',
        Body=json.dumps(payload)
    )
    
    return json.loads(response['Body'].read().decode())