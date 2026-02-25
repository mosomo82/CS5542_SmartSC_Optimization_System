# AWS S3 Automated Data Loading Setup for HyperLogistics
# This script helps configure S3 event notifications for Snowpipe auto-ingestion

import boto3
import json
import os
from dotenv import load_dotenv

load_dotenv()

# AWS Configuration
AWS_REGION = os.getenv('AWS_REGION', 'us-east-1')
S3_BUCKET = os.getenv('S3_BUCKET', 'your-hyperlogistics-bucket')
SNOWFLAKE_ACCOUNT = os.getenv('SNOWFLAKE_ACCOUNT')
SNOWFLAKE_ROLE_ARN = os.getenv('SNOWFLAKE_ROLE_ARN', 'arn:aws:iam::507041536990:role/snowflake_access_role')

def create_s3_bucket_notification():
    """
    Configure S3 bucket notifications to trigger Snowpipe automatically.
    """
    s3_client = boto3.client('s3', region_name=AWS_REGION)

    notification_config = {
        'TopicConfigurations': [],
        'QueueConfigurations': [],
        'LambdaFunctionConfigurations': [],
        'EventBridgeConfiguration': {}
    }

    datasets = [
        {'prefix': 'accidents/',  'pipe': 'ACCIDENTS_PIPE'},
        {'prefix': 'bridges/',    'pipe': 'BRIDGES_PIPE'},
        {'prefix': 'dataco/',     'pipe': 'DATACO_PIPE'},
        {'prefix': 'logistics/',  'pipe': 'LOGISTICS_PIPE'},
    ]

    for dataset in datasets:
        event_config = {
            'Id': f"{dataset['pipe']}-notification",
            'Events': ['s3:ObjectCreated:*'],
            'Filter': {
                'Key': {
                    'FilterRules': [
                        {'Name': 'prefix', 'Value': dataset['prefix']}
                    ]
                }
            }
        }
        print(f"Configured notification for {dataset['prefix']}")
        print(f"Event ID: {event_config['Id']}")
        print("---")

    print("S3 notification configuration prepared.")

def create_s3_bucket_policy():
    """
    Generate S3 bucket policy for Snowflake access.
    """
    if not SNOWFLAKE_ROLE_ARN or SNOWFLAKE_ROLE_ARN.startswith('arn:aws:iam::your-'):
        print("[ERROR] Invalid or placeholder SNOWFLAKE_ROLE_ARN")
        return
    
    bucket_policy = {
        "Version": "2012-10-17",
        "Statement": [
            {
                "Effect": "Allow",
                "Principal": {
                    "AWS": SNOWFLAKE_ROLE_ARN
                },
                "Action": [
                    "s3:GetObject",
                    "s3:GetObjectVersion",
                    "s3:ListBucket"
                ],
                "Resource": [
                    f"arn:aws:s3:::{S3_BUCKET}",
                    f"arn:aws:s3:::{S3_BUCKET}/*"
                ]
            }
        ]
    }

    print("[OK] S3 Bucket Policy for Snowflake:")
    print(json.dumps(bucket_policy, indent=2))
    print(f"[OK] Using Snowflake Role ARN: {SNOWFLAKE_ROLE_ARN}")

    with open('s3_bucket_policy.json', 'w') as f:
        json.dump(bucket_policy, f, indent=2)

    print("[OK] Policy saved to s3_bucket_policy.json")

def generate_upload_script():
    """
    Generate a sample script for uploading datasets to S3.
    """
    upload_script = '''
import boto3
import os
from pathlib import Path
from dotenv import load_dotenv

# Load credentials from .env
load_dotenv()

# Configure AWS credentials
s3_client = boto3.client(
    's3', 
    region_name=os.getenv('AWS_REGION', 'us-east-1'),
    aws_access_key_id=os.getenv('AWS_ACCESS_KEY_ID'),
    aws_secret_access_key=os.getenv('AWS_SECRET_ACCESS_KEY')
)
bucket_name = os.getenv('S3_BUCKET', 'your-hyperlogistics-bucket')

def upload_dataset(local_path, s3_prefix):
    """
    Upload dataset files to S3 with proper prefix.
    """
    if not Path(local_path).exists():
        print(f"[SKIP] {local_path} - directory not found")
        return

    for file_path in Path(local_path).rglob('*'):
        if file_path.is_file():
            s3_key = f"{s3_prefix}/{file_path.name}"
            print(f"Uploading {file_path} to s3://{bucket_name}/{s3_key}")
            try:
                s3_client.upload_file(str(file_path), bucket_name, s3_key)
            except Exception as e:
                print(f"[ERROR] Failed to upload {file_path}: {e}")

# Upload datasets - Core Middle-Mile
upload_dataset('data/accidents', 'accidents')
upload_dataset('data/bridges', 'bridges')

# Upload datasets - Supporting
upload_dataset('data/dataco', 'dataco')
upload_dataset('data/logistics', 'logistics')

print("\\n[SUCCESS] All datasets uploaded to S3.")
'''

    with open('upload_to_s3.py', 'w') as f:
        f.write(upload_script)

    print("Upload script saved to upload_to_s3.py")

if __name__ == "__main__":
    print("HyperLogistics S3 Automation Setup")
    print("-" * 40)

    create_s3_bucket_policy()
    create_s3_bucket_notification()
    generate_upload_script()

    print("\nNext steps:")
    print("1. Apply bucket policy: s3_bucket_policy.json")
    print("2. Run SQL: src/sql/02_setup_s3_automation.sql")
    print("3. Upload data: py upload_to_s3.py")