
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

print("\n[SUCCESS] All datasets uploaded to S3.")
