# ⛽ S3 Quick Reference

A cheat sheet for managing the HyperLogistics data lake.

### 1. Uploading Files
`aws s3 cp data/ s3://hyperlogistics-data/ --recursive`

### 2. Checking Pipe Status
`SELECT SYSTEM$PIPE_STATUS('HYPERLOGISTICS_DB.BRONZE.ACCIDENT_PIPE');`

### 3. Manual Copy Trigger
If Snowpipe is not triggered, run a manual copy:
```sql
COPY INTO HYPERLOGISTICS_DB.BRONZE.BRIDGE_INVENTORY
FROM @HYPERLOGISTICS_DB.BRONZE.BRIDGES_STAGE
FILE_FORMAT = (TYPE = 'CSV' SKIP_HEADER = 1);
```

### 4. Listing Files in Stage
`LIST @HYPERLOGISTICS_DB.BRONZE.ACCIDENTS_STAGE;`
