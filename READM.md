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
