import json
import boto3
import os
from datetime import datetime

sns = boto3.client('sns')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])

def handler(event, context):
    """Process and distribute alerts"""
    try:
        alert_data = event['detail']
        
        # Process alert
        processed_alert = process_alert(alert_data)
        
        # Store alert
        store_alert(processed_alert)
        
        # Send notifications
        send_notifications(processed_alert)
        
        return {
            'statusCode': 200,
            'body': json.dumps('Alert processed successfully')
        }
    except Exception as e:
        print(f"Error processing alert: {str(e)}")
        raise

def process_alert(data):
    """Process alert data"""
    return {
        'alertId': f"alert_{datetime.utcnow().strftime('%Y%m%d%H%M%S')}",
        'timestamp': datetime.utcnow().isoformat(),
        'deviceId': data.get('deviceId'),
        'type': data.get('type', 'unknown'),
        'severity': calculate_severity(data),
        'message': generate_alert_message(data),
        'status': 'new'
    }