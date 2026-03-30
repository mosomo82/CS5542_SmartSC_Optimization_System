# 🚀 S3 Automation Guide

HyperLogistics uses an automated S3-to-Snowpipe pipeline to ingest massive datasets with zero manual intervention.

### 1. AWS Configuration
1. Create an S3 bucket (e.g., `hyperlogistics-data`).
2. Create an IAM Role with `AmazonS3ReadOnlyAccess`.
3. Configure the Trust Relationship to allow your Snowflake account to assume the role.

### 2. Snowflake Security Integration
Create a storage integration in Snowflake to securely connect to your S3 bucket:

```sql
CREATE STORAGE INTEGRATION s3_int
  TYPE = EXTERNAL_STAGE
  STORAGE_PROVIDER = 'S3'
  ENABLED = TRUE
  STORAGE_AWS_ROLE_ARN = 'arn:aws:iam::123456789:role/snowflake-role'
  STORAGE_ALLOWED_LOCATIONS = ('s3://hyperlogistics-data/');
```

### 3. Automating with Snowpipe
Create a pipe that automatically copies data into the Bronze layer when a file lands in S3:

```sql
CREATE OR REPLACE PIPE HYPERLOGISTICS_DB.BRONZE.ACCIDENT_PIPE
AUTO_INGEST = TRUE
AS
COPY INTO HYPERLOGISTICS_DB.BRONZE.TRAFFIC_INCIDENTS
FROM @HYPERLOGISTICS_DB.BRONZE.ACCIDENTS_STAGE;
```

### 4. Running the Pipeline
Once configured, simply run:
`python upload_to_s3.py`
The data will appear in Snowflake within seconds.
