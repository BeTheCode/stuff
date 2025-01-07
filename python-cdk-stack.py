# iot_ml_demo/setup.py
from setuptools import setup, find_packages

setup(
    name="iot_ml_demo",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        "aws-cdk-lib>=2.0.0",
        "constructs>=10.0.0",
    ],
)

# iot_ml_demo/app.py
import aws_cdk as cdk
from iot_ml_demo.iot_ml_demo_stack import IoTMLDemoStack

app = cdk.App()
IoTMLDemoStack(app, "IoTMLDemoStack")
app.synth()

# iot_ml_demo/iot_ml_demo_stack.py
import aws_cdk as cdk
from constructs import Construct
from aws_cdk import (
    aws_iot as iot,
    aws_s3 as s3,
    aws_lambda as lambda_,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
    aws_apigateway as apigateway,
    aws_sagemaker as sagemaker,
    RemovalPolicy,
    Duration,
    CfnOutput
)

class IoTMLDemoStack(cdk.Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # S3 Buckets for raw and processed data
        raw_data_bucket = s3.Bucket(
            self, 'RawDataBucket',
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            versioned=True
        )

        processed_data_bucket = s3.Bucket(
            self, 'ProcessedDataBucket',
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            versioned=True
        )

        # DynamoDB table for storing analysis results
        analysis_table = dynamodb.Table(
            self, 'AnalysisTable',
            partition_key=dynamodb.Attribute(
                name='deviceId',
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name='timestamp',
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY
        )

        # Lambda for data preprocessing
        preprocessor_lambda = lambda_.Function(
            self, 'PreprocessorLambda',
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler='preprocessor.handler',
            code=lambda_.Code.from_asset('lambda/preprocessor'),
            environment={
                'PROCESSED_BUCKET_NAME': processed_data_bucket.bucket_name,
                'DYNAMODB_TABLE': analysis_table.table_name
            },
            timeout=Duration.minutes(5),
            memory_size=1024
        )

        # Lambda for image analysis
        image_analysis_lambda = lambda_.Function(
            self, 'ImageAnalysisLambda',
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler='image_analysis.handler',
            code=lambda_.Code.from_asset('lambda/image_analysis'),
            environment={
                'DYNAMODB_TABLE': analysis_table.table_name
            },
            timeout=Duration.minutes(5),
            memory_size=1024
        )

        # IoT Core Rule Role
        iot_role_for_s3 = iam.Role(
            self, 'IoTRoleForS3',
            assumed_by=iam.ServicePrincipal('iot.amazonaws.com')
        )

        # IoT Core Rule
        iot_topic_rule = iot.CfnTopicRule(
            self, 'IoTIngestRule',
            topic_rule_payload=iot.CfnTopicRule.TopicRulePayloadProperty(
                sql="SELECT * FROM 'manufacturing/sensors/#'",
                actions=[iot.CfnTopicRule.ActionProperty(
                    s3=iot.CfnTopicRule.S3ActionProperty(
                        bucket_name=raw_data_bucket.bucket_name,
                        role_arn=iot_role_for_s3.role_arn,
                        key='${topic()}/${timestamp()}.json'
                    )
                )]
            )
        )

        # API Gateway
        api = apigateway.RestApi(
            self, 'DemoApi',
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS
            )
        )

        # Lambda for API backend
        api_backend_lambda = lambda_.Function(
            self, 'ApiBackendLambda',
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler='api.handler',
            code=lambda_.Code.from_asset('lambda/api'),
            environment={
                'DYNAMODB_TABLE': analysis_table.table_name
            }
        )

        # API Gateway Integration
        integration = apigateway.LambdaIntegration(api_backend_lambda)
        api.root.add_method('GET', integration)
        api.root.add_resource('analysis').add_method('GET', integration)

        # Grant necessary permissions
        raw_data_bucket.grant_read(preprocessor_lambda)
        processed_data_bucket.grant_write(preprocessor_lambda)
        analysis_table.grant_read_write_data(preprocessor_lambda)
        analysis_table.grant_read_write_data(image_analysis_lambda)
        analysis_table.grant_read_data(api_backend_lambda)
        raw_data_bucket.grant_write(iot_role_for_s3)

        # Output important values
        CfnOutput(self, 'ApiUrl', value=api.url)
        CfnOutput(self, 'RawDataBucketName', value=raw_data_bucket.bucket_name)
        CfnOutput(self, 'ProcessedDataBucketName', value=processed_data_bucket.bucket_name)
        CfnOutput(self, 'DynamoDBTableName', value=analysis_table.table_name)

# README.md
# IoT ML Demo Infrastructure

This repository contains AWS CDK code in Python for deploying an IoT ML infrastructure stack.

## Prerequisites

- Python 3.9 or later
- AWS CLI configured with appropriate credentials
- AWS CDK CLI installed (`npm install -g aws-cdk`)
- Node.js and npm (for CDK CLI)

## Project Structure
```
iot_ml_demo/
├── lambda/
│   ├── preprocessor/
│   │   └── preprocessor.py
│   ├── image_analysis/
│   │   └── image_analysis.py
│   └── api/
│       └── api.py
├── iot_ml_demo/
│   ├── __init__.py
│   └── iot_ml_demo_stack.py
├── app.py
├── setup.py
├── requirements.txt
└── README.md
```

## Setup Instructions

1. Create and activate a virtual environment:
```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
pip install -e .
```

3. Bootstrap CDK (if not already done in your AWS account/region):
```bash
cdk bootstrap
```

4. Deploy the stack:
```bash
cdk deploy
```

## Teardown Instructions

1. To destroy the stack and clean up all resources:
```bash
cdk destroy
```

2. Confirm the deletion when prompted

Note: The S3 buckets and DynamoDB table are set with RemovalPolicy.DESTROY, so they will be automatically deleted during teardown.

## Available Resources

After deployment, the following resources will be created:
- Two S3 buckets (raw and processed data)
- DynamoDB table for analysis results
- Lambda functions for preprocessing and image analysis
- IoT Core Rule for data ingestion
- API Gateway with Lambda integration
- Required IAM roles and permissions

## Important Notes

- Ensure your AWS credentials have sufficient permissions
- The stack outputs important values like API URL and bucket names
- All resources are configured for automatic cleanup on stack destruction
- Lambda function code should be placed in the respective directories under /lambda
