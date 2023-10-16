##------------------------------------------##
##-- main.py
##------------------------------------------## 
    
import os
import json
import boto3
import hashlib
import requests
import numpy as np
import pandas as pd
from pandas import json_normalize
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from botocore.exceptions import ClientError

from aws_cdk import core
from aws_cdk import aws_lambda as _lambda
from aws_cdk import aws_sqs as sqs
from aws_cdk import aws_s3 as s3
from aws_cdk import aws_events as events
from aws_cdk import aws_events_targets as targets
from aws_cdk import aws_iam as iam
from aws_cdk import aws_s3_notifications
from aws_cdk.aws_s3_notifications import SqsDestination


##-- Initialize Spark session
# os.environ['PYARROW_IGNORE_TIMEZONE'] = '1'
# from pyspark.sql import SparkSession
# import pyspark.pandas as ps
# from pyspark.sql import functions as F
# from pyspark.sql.window import Window
# spark = SparkSession.builder.appName("LoadData").getOrCreate()        
# spark.sparkContext.setLogLevel("ERROR")

##------------------------------------------##
##-- Load AWS Configurations
##------------------------------------------##
info = (lambda f: json.load(f))(open("info.txt", 'r'))
    
AWS_ACCESS_KEY = info["secrets"]["AWS_ACCESS_KEY"]
AWS_SECRET_ACCESS = info["secrets"]["AWS_SECRET_ACCESS"]
AWS_ARN = info["secrets"]["AWS_ARN"]
AWS_REGION = info["secrets"]["AWS_REGION"]

S3_BUCKET = info['pipeline']["S3_BUCKET"]
SQS_QUEUE = info['pipeline']["SQS_QUEUE"] 
LAMBDA_P1_P2 = info['pipeline']["LAMBDA_P1_P2"]
LAMBDA_P3 = info['pipeline']["LAMBDA_P3"]

##------------------------------------------##
##-- Initialize AWS Clients
##------------------------------------------##

s3_client = boto3.client(
    's3',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_ACCESS,
    region_name=AWS_REGION
)

lambda_client = boto3.client(
    'lambda',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_ACCESS,
    region_name=AWS_REGION
)

sqs_client = boto3.client(
    'sqs',
    aws_access_key_id=AWS_ACCESS_KEY,
    aws_secret_access_key=AWS_SECRET_ACCESS,
    region_name=AWS_REGION
)

##------------------------------------------##
##-- Verify Resources - Functions
##------------------------------------------##

def verify_sqs_queue(sqs_client,queue_name):
    try:
        response = sqs_client.get_queue_url(QueueName=queue_name)
        print(f"\nQueue {queue_name} already exists: \n{response['QueueUrl']}")
        return True
    except ClientError as e:
        if e.response['Error']['Code'] == 'AWS.SimpleQueueService.NonExistentQueue':
            print(f"\nQueue {queue_name} does not exist. Creating...")
            response = sqs_client.create_queue(QueueName=queue_name)
            print(f"\nQueue {queue_name} created: \n{response['QueueUrl']}")
            return True
        else:
            print(f"\nAn error occurred: {e}")
            return False
        
def verify_bucket(s3_client,bucket_name):
    try:
        response = s3_client.head_bucket(Bucket=bucket_name)
        response_server = response["ResponseMetadata"]["HTTPHeaders"]["server"]
        print(f"\nBucket {bucket_name} exists: \n{response_server}")
        return True
    except ClientError:
        return False
    
def verify_lambda_function(lambda_client,function_name):
    
    try:
        lambda_client.get_function(FunctionName=function_name)
        print(f"\nFunction {function_name} already exists.")
        return True
    except lambda_client.exceptions.ResourceNotFoundException:
        try:
            with open(f"{function_name}.zip", 'rb') as f:
                zipped_code = f.read()
                
            lambda_client.create_function(
                FunctionName=function_name,
                Role=AWS_ARN,
                Handler=f"{function_name}.handler",
                Code={'ZipFile': zipped_code},
                Runtime='python3.8'
            )
            
            print(f"Function {function_name} created.")
            return True
        except Exception as e:
            print(f"Failed to create function {function_name}: {e}")
            return False

##------------------------------------------##
##-- Verify Resources - Main Function
##------------------------------------------##

def verify_resource(client, resource_name, create_fn):
    try:
        create_fn(client, resource_name)
        # print(f"\nSuccessfully verified:\n{resource_name}\n")
        return True
    except ClientError as e:
        print(f"\nFailed to verify:\n{resource_name}: {e}\n")
        return False


##------------------------------------------##
##-- Build CDK
##------------------------------------------##
class DataPipelineStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)
        
        ##------------------------------------------##
        ##-- Verify Resources
        ##------------------------------------------##
        verify_resource(lambda_client, LAMBDA_P1_P2, verify_lambda_function)
        verify_resource(lambda_client, LAMBDA_P3, verify_lambda_function)
        verify_resource(sqs_client, SQS_QUEUE, verify_sqs_queue)
        verify_resource(s3_client, S3_BUCKET, verify_bucket)
        
        ##------------------------------------------##
        ##-- Lambda Function (Part1 & Part2)
        ##------------------------------------------##
        AWS_ARN_ADMIN = iam.Role.from_role_arn(self, "Role", AWS_ARN)
        lambda_part1_2 = _lambda.Function(self, 
				f"{LAMBDA_P1_P2}",
				role= AWS_ARN_ADMIN,
				handler=f"{LAMBDA_P1_P2}.handler",
				code=_lambda.Code.from_asset(f"{LAMBDA_P1_P2}.zip"),
				runtime=_lambda.Runtime.PYTHON_3_8)

        ##------------------------------------------##
        ##-- Schedule Lambda Function (Part1 & Part2) 
        ##-- Runs daily @ 12:00 UTC
        ##------------------------------------------##
        events.Rule(
		self, "Rule",
		schedule=events.Schedule.cron(minute='0', hour='12'),
		targets=[targets.LambdaFunction(lambda_part1_2)]
	)
        
        ##------------------------------------------##
        ##-- Lambda Function (Part1 & Part2)
        ##------------------------------------------##
        lambda_part3 = _lambda.Function(self, 
				f"{LAMBDA_P3}",
				role= AWS_ARN_ADMIN,
				handler=f"{LAMBDA_P3}.handler",
				code=_lambda.Code.from_asset(f"{LAMBDA_P3}.zip"),
				runtime=_lambda.Runtime.PYTHON_3_8)
        
        ##------------------------------------------##    
        ##-- SQS Queue >> Trigger Lambda Function (Part3)
        ##------------------------------------------##
        data_queue = sqs.Queue(self, f"{SQS_QUEUE}")
        data_queue.grant_send_messages(lambda_part3)
        
        ##------------------------------------------##
        ##-- S3 Bucket >> S3 Event to SQS
        ##------------------------------------------##
        data_bucket = s3.Bucket(self, f"{S3_BUCKET}")
        #data_bucket.add_event_notification(s3.EventType.OBJECT_CREATED,s3_notifications.SqsDestination(data_queue))
        data_bucket.add_event_notification(s3.EventType.OBJECT_CREATED, SqsDestination(data_queue))

##------------------------------------------##
if __name__ == '__main__':
    app = core.App()
    DataPipelineStack(app, "DataPipelineStack")
    app.synth()