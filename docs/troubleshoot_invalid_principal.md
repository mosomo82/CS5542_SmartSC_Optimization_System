# 🛡️ Troubleshooting: Invalid Principal

This error occurs when the IAM role trust relationship is not properly configured for Snowflake.

### 1. Symptom
`SQL Error: Storage Integration 'S3_INT' is not authorized to access S3 bucket.`

### 2. Fix: Update Trust Policy
1. Run `DESC INTEGRATION s3_int;` in Snowflake.
2. Note the `STORAGE_AWS_IAM_USER_ARN` and `STORAGE_AWS_EXTERNAL_ID`.
3. Go to **AWS Console > IAM > Roles > YourSnowflakeRole**.
4. Update the **Trust Relationship** policy:

```json
{
  "Version": "2012-10-17",
  "Statement": [{
    "Effect": "Allow",
    "Principal": { "AWS": "STORAGE_AWS_IAM_USER_ARN" },
    "Action": "sts:AssumeRole",
    "Condition": { "StringEquals": { "sts:ExternalId": "STORAGE_AWS_EXTERNAL_ID" } }
  }]
}
```
5. Save and retry the Snowflake command.
