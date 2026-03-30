#!/bin/bash
read -p "Enter S3 Bucket Name: " BUCKET_NAME
echo "Creating bucket $BUCKET_NAME..."
aws s3 mb s3://$BUCKET_NAME
if [ $? -ne 0 ]; then
    echo "[ERROR] Failed to create bucket. Check your AWS permissions."
    exit 1
fi
echo "[SUCCESS] Bucket s3://$BUCKET_NAME created."
