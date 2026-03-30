# ❄️ Snowflake Setup Guide

This guide provides instructions for setting up the Snowflake environment for HyperLogistics.

### 1. Core Database Structure
Run the following SQL in a Snowflake worksheet to create the Medallion architecture:

```sql
CREATE DATABASE IF NOT EXISTS HYPERLOGISTICS_DB;
CREATE SCHEMA IF NOT EXISTS HYPERLOGISTICS_DB.BRONZE;
CREATE SCHEMA IF NOT EXISTS HYPERLOGISTICS_DB.SILVER;
CREATE SCHEMA IF NOT EXISTS HYPERLOGISTICS_DB.GOLD;
```

### 2. Required Stages
For data loading via S3 or local files, you need to define stages:

```sql
CREATE OR REPLACE STAGE HYPERLOGISTICS_DB.BRONZE.ACCIDENTS_STAGE;
CREATE OR REPLACE STAGE HYPERLOGISTICS_DB.BRONZE.BRIDGES_STAGE;
```

### 3. Cortex LLM Access
Ensure your role has access to `SNOWFLAKE.CORTEX.COMPLETE`. If you encounter permission errors, run:

```sql
GRANT DATABASE ROLE SNOWFLAKE.CORTEX_USER TO ROLE your_role_name;
```

### 4. Verification
Check that your tables are populated after running the ingestion scripts:
```sql
SELECT COUNT(*) FROM HYPERLOGISTICS_DB.BRONZE.TRAFFIC_INCIDENTS;
```
