import json
import boto3
import os
from datetime import datetime
import numpy as np
from boto3.dynamodb.conditions import Key

s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])
bedrock = boto3.client('bedrock-runtime')

def handler(event, context):
    """Process incoming IoT data"""
    try:
        # Extract records from IoT Core Rule
        records = event['Records']
        
        for record in records:
            # Parse S3 event
            bucket = record['s3']['bucket']['name']
            key = record['s3']['object']['key']
            
            # Get data from S3
            response = s3.get_object(Bucket=bucket, Key=key)
            data = json.loads(response['Body'].read().decode('utf-8'))
            
            # Process the data
            processed_data = process_sensor_data(data)
            
            # Store processed data
            store_processed_data(processed_data)
            
            # Check for anomalies
            if is_anomaly(processed_data):
                trigger_anomaly_processing(processed_data)
        
        return {
            'statusCode': 200,
            'body': json.dumps('Processing completed successfully')
        }
    except Exception as e:
        print(f"Error processing data: {str(e)}")
        raise

def process_sensor_data(data):
    """Process raw sensor data"""
    return {
        'deviceId': data['device_id'],
        'timestamp': data.get('timestamp', datetime.utcnow().isoformat()),
        'temperature': analyze_temperature(data.get('temperature', 0)),
        'vibration': analyze_vibration(data.get('vibration', 0)),
        'processed': True,
        'processedAt': datetime.utcnow().isoformat()
    }

def analyze_temperature(temp):
    """Analyze temperature readings"""
    return {
        'value': temp,
        'status': 'critical' if temp > 85 else 'warning' if temp > 75 else 'normal',
        'threshold': 75
    }

def analyze_vibration(vib):
    """Analyze vibration readings"""
    return {
        'value': vib,
        'status': 'critical' if vib > 0.8 else 'warning' if vib > 0.5 else 'normal',
        'threshold': 0.5
    }