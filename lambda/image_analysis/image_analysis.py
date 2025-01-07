import json
import boto3
import os
from datetime import datetime
import base64

rekognition = boto3.client('rekognition')
s3 = boto3.client('s3')
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['DYNAMODB_TABLE'])

def handler(event, context):
    """Process images from IoT devices"""
    try:
        records = event['Records']
        
        for record in records:
            # Get image from S3
            bucket = record['s3']['bucket']['name']
            key = record['s3']['object']['key']
            
            # Analyze image
            analysis = analyze_image(bucket, key)
            
            # Store results
            store_analysis_results(analysis)
            
            # Check for defects
            if has_defects(analysis):
                trigger_defect_alert(analysis)
        
        return {
            'statusCode': 200,
            'body': json.dumps('Image analysis completed')
        }
    except Exception as e:
        print(f"Error analyzing image: {str(e)}")
        raise

def analyze_image(bucket, key):
    """Analyze image using Rekognition"""
    response = rekognition.detect_labels(
        Image={'S3Object': {'Bucket': bucket, 'Name': key}},
        MaxLabels=10,
        MinConfidence=70
    )
    
    return {
        'imageKey': key,
        'timestamp': datetime.utcnow().isoformat(),
        'labels': response['Labels'],
        'confidence': max([label['Confidence'] for label in response['Labels']], default=0),
        'analysisType': 'quality_control'
    }
