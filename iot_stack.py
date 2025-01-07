from aws_cdk import (
    Stack,
    Duration,
    CfnOutput,
    RemovalPolicy,
    aws_iot as iot,
    aws_s3 as s3,
    aws_lambda as lambda_,
    aws_dynamodb as dynamodb,
    aws_iam as iam,
    aws_apigateway as apigateway,
    aws_sagemaker as sagemaker,
    aws_sns as sns,
    aws_cloudwatch as cloudwatch,
    aws_events as events,
    aws_events_targets as targets
)
from constructs import Construct
import os

class IoTMLStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # S3 Buckets
        self.raw_data_bucket = s3.Bucket(
            self, 'RawDataBucket',
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            versioned=True,
            lifecycle_rules=[
                s3.LifecycleRule(
                    transitions=[
                        s3.Transition(
                            storage_class=s3.StorageClass.INFREQUENT_ACCESS,
                            transition_after=Duration.days(30)
                        )
                    ]
                )
            ]
        )

        self.processed_data_bucket = s3.Bucket(
            self, 'ProcessedDataBucket',
            removal_policy=RemovalPolicy.DESTROY,
            auto_delete_objects=True,
            versioned=True
        )

        # DynamoDB Tables
        self.device_table = dynamodb.Table(
            self, 'DeviceTable',
            partition_key=dynamodb.Attribute(
                name='deviceId',
                type=dynamodb.AttributeType.STRING
            ),
            sort_key=dynamodb.Attribute(
                name='timestamp',
                type=dynamodb.AttributeType.STRING
            ),
            billing_mode=dynamodb.BillingMode.PAY_PER_REQUEST,
            removal_policy=RemovalPolicy.DESTROY,
            time_to_live_attribute='ttl',
            stream_specification=dynamodb.StreamViewType.NEW_AND_OLD_IMAGES
        )

        # SNS Topics
        self.alert_topic = sns.Topic(
            self, 'AlertTopic',
            display_name='IoT Alerts'
        )

        # Lambda Functions
        self.preprocessor_lambda = self.create_lambda(
            'PreprocessorLambda',
            'lambda/preprocessor',
            'preprocessor.handler',
            {
                'PROCESSED_BUCKET': self.processed_data_bucket.bucket_name,
                'DEVICE_TABLE': self.device_table.table_name,
                'ALERT_TOPIC': self.alert_topic.topic_arn
            }
        )

        self.image_analysis_lambda = self.create_lambda(
            'ImageAnalysisLambda',
            'lambda/image_analysis',
            'image_analysis.handler',
            {
                'DEVICE_TABLE': self.device_table.table_name,
                'ALERT_TOPIC': self.alert_topic.topic_arn
            }
        )

        self.alert_lambda = self.create_lambda(
            'AlertLambda',
            'lambda/alert_processor',
            'alert_processor.handler',
            {
                'DEVICE_TABLE': self.device_table.table_name,
                'ALERT_TOPIC': self.alert_topic.topic_arn
            }
        )

        self.api_lambda = self.create_lambda(
            'ApiLambda',
            'lambda/api',
            'api.handler',
            {
                'DEVICE_TABLE': self.device_table.table_name
            }
        )

        self.ml_lambda = self.create_lambda(
            'MLLambda',
            'lambda/ml_processor',
            'ml_processor.handler',
            {
                'DEVICE_TABLE': self.device_table.table_name,
                'ALERT_TOPIC': self.alert_topic.topic_arn
            }
        )

        # API Gateway
        api = apigateway.RestApi(
            self, 'IoTAPI',
            rest_api_name='IoT ML API',
            description='IoT ML Demo API',
            deploy_options=apigateway.StageOptions(
                stage_name='prod',
                throttling_rate_limit=10,
                throttling_burst_limit=20
            ),
            default_cors_preflight_options=apigateway.CorsOptions(
                allow_origins=apigateway.Cors.ALL_ORIGINS,
                allow_methods=apigateway.Cors.ALL_METHODS
            )
        )

        api_integration = apigateway.LambdaIntegration(self.api_lambda)
        api.root.add_method('GET', api_integration)
        
        devices = api.root.add_resource('devices')
        devices.add_method('GET', api_integration)
        
        analysis = api.root.add_resource('analysis')
        analysis.add_method('GET', api_integration)

        # IoT Rule
        iot_role = iam.Role(
            self, 'IoTRole',
            assumed_by=iam.ServicePrincipal('iot.amazonaws.com')
        )

        iot_topic_rule = iot.CfnTopicRule(
            self, 'IoTIngestRule',
            topic_rule_payload=iot.CfnTopicRule.TopicRulePayloadProperty(
                sql="SELECT * FROM 'manufacturing/sensors/#'",
                actions=[
                    iot.CfnTopicRule.ActionProperty(
                        lambda_=iot.CfnTopicRule.LambdaActionProperty(
                            function_arn=self.preprocessor_lambda.function_arn
                        )
                    )
                ]
            )
        )

        # CloudWatch Alarms
        error_alarm = cloudwatch.Alarm(
            self, 'ErrorAlarm',
            metric=self.preprocessor_lambda.metric_errors(),
            threshold=5,
            evaluation_periods=1,
            alarm_description='Alert on preprocessing errors'
        )

        # Outputs
        CfnOutput(self, 'ApiUrl', value=api.url)
        CfnOutput(self, 'RawDataBucket', value=self.raw_data_bucket.bucket_name)
        CfnOutput(self, 'ProcessedDataBucket', 
                 value=self.processed_data_bucket.bucket_name)
        CfnOutput(self, 'AlertTopicArn', value=self.alert_topic.topic_arn)

    def create_lambda(self, id: str, code_path: str, handler: str, 
                     environment: dict) -> lambda_.Function:
        """Helper method to create Lambda functions with consistent settings"""
        return lambda_.Function(
            self, id,
            runtime=lambda_.Runtime.PYTHON_3_9,
            handler=handler,
            code=lambda_.Code.from_asset(code_path),
            environment=environment,
            timeout=Duration.minutes(5),
            memory_size=1024,
            tracing=lambda_.Tracing.ACTIVE,
            retry_attempts=2
        )