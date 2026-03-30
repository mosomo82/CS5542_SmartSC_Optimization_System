@echo off
set /p BUCKET_NAME="Enter S3 Bucket Name: "
echo Creating bucket %BUCKET_NAME%...
aws s3 mb s3://%BUCKET_NAME%
if %ERRORLEVEL% NEQ 0 (
    echo [ERROR] Failed to create bucket. Check your AWS permissions.
    exit /b 1
)
echo [SUCCESS] Bucket s3://%BUCKET_NAME% created.
