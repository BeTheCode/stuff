import json
import boto3
import os
from datetime import datetime
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)

def store_processed_data(data):
    """Store processed data in DynamoDB"""
    try:
        table = get_dynamodb_table()
        table.put_item(Item=data)
    except Exception as e:
        logger.error(f"Error storing data: {str(e)}")
        raise

def trigger_anomaly_processing(data):
    """Trigger anomaly processing workflow"""
    try:
        sns = boto3.client('sns')
        topic_arn = os.environ['ANOMALY_TOPIC_ARN']
        
        sns.publish(
            TopicArn=topic_arn,
            Message=json.dumps(data),
            MessageAttributes={
                'type': {
                    'DataType': 'String',
                    'StringValue': 'anomaly'
                }
            }
        )
    except Exception as e:
        logger.error(f"Error triggering anomaly processing: {str(e)}")
        raise

def get_dynamodb_table():
    """Get DynamoDB table reference"""
    dynamodb = boto3.resource('dynamodb')
    return dynamodb.Table(os.environ['DYNAMODB_TABLE'])

def calculate_severity(data):
    """Calculate alert severity"""
    if data.get('temperature', {}).get('status') == 'critical' or \
       data.get('vibration', {}).get('status') == 'critical':
        return 'critical'
    elif data.get('temperature', {}).get('status') == 'warning' or \
         data.get('vibration', {}).get('status') == 'warning':
        return 'warning'
    return 'info'

def generate_alert_message(data):
    """Generate human-readable alert message"""
    messages = []
    
    if 'temperature' in data:
        temp = data['temperature']
        if temp['status'] != 'normal':
            messages.append(
                f"Temperature {temp['value']}°C exceeds threshold {temp['threshold']}°C"
            )
    
    if 'vibration' in data:
        vib = data['vibration']
        if vib['status'] != 'normal':
            messages.append(
                f"Vibration {vib['value']}g exceeds threshold {vib['threshold']}g"
            )
    
    return ' and '.join(messages) if messages else 'No specific issues detected'

def format_response(status_code, body):
    """Format API response"""
    return {
        'statusCode': status_code,
        'headers': {
            'Content-Type': 'application/json',
            'Access-Control-Allow-Origin': '*'
        },
        'body': json.dumps(body)
    }