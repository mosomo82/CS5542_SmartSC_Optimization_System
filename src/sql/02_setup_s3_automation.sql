-- Automated S3 Data Loading Setup for HyperLogistics
-- IMPORTANT: Run 00_create_database.sql FIRST!
-- Then run this script to set up Snowpipe auto-ingestion
--
-- Datasets & S3 Paths:
--   Core #1: US Accidents       → s3://bucket/accidents/       → BRONZE.TRAFFIC_INCIDENTS
--   Core #3: Bridge Inventory   → s3://bucket/bridges/         → BRONZE.BRIDGE_INVENTORY
--   Core #2: NOAA GSOD          → (External Table in 01_setup_noaa.sql)
--   Supporting #4: DataCo       → s3://bucket/dataco/          → BRONZE.RAW_LOGISTICS
--   Supporting #5: Logistics Ops→ s3://bucket/logistics/   → BRONZE.LOGISTICS  

-- Prerequisites:
-- 1. Database and schemas already created (00_create_database.sql)
-- 2. Tables already exist in BRONZE layer
-- 3. AWS S3 bucket created with structure: /accidents/, /bridges/, /dataco/, /logistics/
-- 4. Snowflake IAM role with S3 access created in AWS
-- 5. Bucket policy applied

-- IMPORTANT: Replace the following placeholders:
-- - 'your-hyperlogistics-bucket' → Your actual S3 bucket name
-- - 'arn:aws:iam::507041536990:role/snowflake_access_role' → Your actual role ARN
--   NOTE: Role is in account 507041536990 (cross-account setup)
--   For instructions on cross-account access, see: docs/option_b_cross_account_setup.md

-- Set context
USE DATABASE HYPERLOGISTICS_DB;
USE SCHEMA BRONZE;

-- ═══════════════════════════════════════════════════════════════
-- CORE MIDDLE-MILE STAGES & PIPES
-- ═══════════════════════════════════════════════════════════════

-- [Core #1] US Accidents → Data Perception Layer
-- Snowpipe provides near-real-time ingestion of accident data
CREATE OR REPLACE STAGE HYPERLOGISTICS_DB.BRONZE.ACCIDENTS_STAGE
URL = 's3://your-hyperlogistics-bucket/accidents/'
STORAGE_INTEGRATION = S3_INTEGRATION
FILE_FORMAT = (TYPE = CSV, SKIP_HEADER = 1, FIELD_DELIMITER = ',', FIELD_OPTIONALLY_ENCLOSED_BY = '"');

CREATE OR REPLACE PIPE HYPERLOGISTICS_DB.BRONZE.ACCIDENTS_PIPE AUTO_INGEST = TRUE
AS COPY INTO HYPERLOGISTICS_DB.BRONZE.TRAFFIC_INCIDENTS
FROM @HYPERLOGISTICS_DB.BRONZE.ACCIDENTS_STAGE
FILE_FORMAT = (TYPE = CSV, SKIP_HEADER = 1, FIELD_DELIMITER = ',', FIELD_OPTIONALLY_ENCLOSED_BY = '"')
ON_ERROR = 'CONTINUE';

-- [Core #2] NOAA GSOD → Intelligence & Forecasting Layer
-- External Table created in 01_setup_noaa.sql (no stage/pipe needed here)

-- [Core #3] National Bridge Inventory → Validation & Safety Layer
-- Batch-loaded; relatively static data (~600K records, updated annually by US DOT)
CREATE OR REPLACE STAGE HYPERLOGISTICS_DB.BRONZE.BRIDGES_STAGE
URL = 's3://your-hyperlogistics-bucket/bridges/'
STORAGE_INTEGRATION = S3_INTEGRATION
FILE_FORMAT = (TYPE = CSV, SKIP_HEADER = 1, FIELD_DELIMITER = ',', FIELD_OPTIONALLY_ENCLOSED_BY = '"');

CREATE OR REPLACE PIPE HYPERLOGISTICS_DB.BRONZE.BRIDGES_PIPE AUTO_INGEST = TRUE
AS COPY INTO HYPERLOGISTICS_DB.BRONZE.BRIDGE_INVENTORY
FROM @HYPERLOGISTICS_DB.BRONZE.BRIDGES_STAGE
FILE_FORMAT = (TYPE = CSV, SKIP_HEADER = 1, FIELD_DELIMITER = ',', FIELD_OPTIONALLY_ENCLOSED_BY = '"')
ON_ERROR = 'CONTINUE';

-- ═══════════════════════════════════════════════════════════════
-- SUPPORTING DATASET STAGES & PIPES
-- ═══════════════════════════════════════════════════════════════

-- [Supporting #4] DataCo Supply Chain → SRSNet Training Only
CREATE OR REPLACE STAGE HYPERLOGISTICS_DB.BRONZE.DATACO_STAGE
URL = 's3://your-hyperlogistics-bucket/dataco/'
STORAGE_INTEGRATION = S3_INTEGRATION
FILE_FORMAT = (TYPE = CSV, SKIP_HEADER = 1, FIELD_DELIMITER = ',', FIELD_OPTIONALLY_ENCLOSED_BY = '"');

CREATE OR REPLACE PIPE HYPERLOGISTICS_DB.BRONZE.DATACO_PIPE AUTO_INGEST = TRUE
AS COPY INTO HYPERLOGISTICS_DB.BRONZE.RAW_LOGISTICS
FROM @HYPERLOGISTICS_DB.BRONZE.DATACO_STAGE
FILE_FORMAT = (TYPE = CSV, SKIP_HEADER = 1, FIELD_DELIMITER = ',', FIELD_OPTIONALLY_ENCLOSED_BY = '"')
ON_ERROR = 'CONTINUE';

-- [Supporting #5] Logistics Operations Database → RAG Knowledge Base
CREATE OR REPLACE STAGE HYPERLOGISTICS_DB.BRONZE.LOGISTICS_STAGE
URL = 's3://your-hyperlogistics-bucket/logistics/'
STORAGE_INTEGRATION = S3_INTEGRATION
FILE_FORMAT = (TYPE = CSV, SKIP_HEADER = 1, FIELD_DELIMITER = ',', FIELD_OPTIONALLY_ENCLOSED_BY = '"');

CREATE OR REPLACE PIPE HYPERLOGISTICS_DB.BRONZE.LOGISTICS_PIPE AUTO_INGEST = TRUE
AS COPY INTO HYPERLOGISTICS_DB.BRONZE.LOGISTICS
FROM @HYPERLOGISTICS_DB.BRONZE.LOGISTICS_STAGE
FILE_FORMAT = (TYPE = CSV, SKIP_HEADER = 1, FIELD_DELIMITER = ',', FIELD_OPTIONALLY_ENCLOSED_BY = '"')
ON_ERROR = 'CONTINUE';

-- ═══════════════════════════════════════════════════════════════
-- PERMISSIONS
-- ═══════════════════════════════════════════════════════════════

-- Stage permissions
GRANT USAGE ON STAGE HYPERLOGISTICS_DB.BRONZE.ACCIDENTS_STAGE TO ROLE SYSADMIN;
GRANT USAGE ON STAGE HYPERLOGISTICS_DB.BRONZE.BRIDGES_STAGE TO ROLE SYSADMIN;
GRANT USAGE ON STAGE HYPERLOGISTICS_DB.BRONZE.NOAA_S3_STAGE TO ROLE SYSADMIN;
GRANT USAGE ON STAGE HYPERLOGISTICS_DB.BRONZE.DATACO_STAGE TO ROLE SYSADMIN;
GRANT USAGE ON STAGE HYPERLOGISTICS_DB.BRONZE.LOGISTICS_STAGE TO ROLE SYSADMIN;

-- Pipe permissions
GRANT MONITOR, OPERATE ON PIPE HYPERLOGISTICS_DB.BRONZE.ACCIDENTS_PIPE TO ROLE SYSADMIN;
GRANT MONITOR, OPERATE ON PIPE HYPERLOGISTICS_DB.BRONZE.BRIDGES_PIPE TO ROLE SYSADMIN;
GRANT MONITOR, OPERATE ON PIPE HYPERLOGISTICS_DB.BRONZE.DATACO_PIPE TO ROLE SYSADMIN;
GRANT MONITOR, OPERATE ON PIPE HYPERLOGISTICS_DB.BRONZE.LOGISTICS_PIPE TO ROLE SYSADMIN;

-- Verify pipe status
SELECT PIPE_NAME, DEFINITION, IS_AUTOINGEST_ENABLED
FROM INFORMATION_SCHEMA.PIPES
WHERE PIPE_SCHEMA = 'BRONZE'
ORDER BY PIPE_NAME;