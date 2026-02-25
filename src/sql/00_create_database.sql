-- HyperLogistics Database Setup
-- Run this FIRST before other SQL scripts
-- Creates the database, schemas, and base tables
--
-- Core Middle-Mile Datasets:
--   1. US Accidents (2016-2023)  → BRONZE.TRAFFIC_INCIDENTS  → SILVER.RISK_HEATMAP      [Data Perception Layer]
--   2. NOAA GSOD (Weather)      → BRONZE.NOAA_GSOD (ext.)   → SILVER.WEATHER_ALERTS     [Intelligence & Forecasting Layer]
--   3. National Bridge Inventory → BRONZE.BRIDGE_INVENTORY   → SILVER.BRIDGE_INVENTORY_GEO [Validation & Safety Layer]
--
-- Supporting Datasets:
--   4. DataCo Supply Chain      → BRONZE.RAW_LOGISTICS      → SILVER.CLEANED_LOGISTICS  [SRSNet Training Only]
--   5. Logistics Operations DB  → BRONZE.LOGISTICS           → SILVER.LOGISTICS_VECTORIZED [RAG Knowledge Base]

-- Set context
USE ROLE SYSADMIN;
USE WAREHOUSE COMPUTE_WH;

-- 1. Create Database
CREATE DATABASE IF NOT EXISTS HYPERLOGISTICS_DB;

-- 2. Create Schemas (Medallion Architecture)
CREATE SCHEMA IF NOT EXISTS HYPERLOGISTICS_DB.BRONZE;
CREATE SCHEMA IF NOT EXISTS HYPERLOGISTICS_DB.SILVER;
CREATE SCHEMA IF NOT EXISTS HYPERLOGISTICS_DB.GOLD;

-- 3. Create Bronze Layer Tables (Raw Data)

-- ═══════════════════════════════════════════════════════════════
-- CORE MIDDLE-MILE TABLES
-- ═══════════════════════════════════════════════════════════════

-- [Core #1] US Accidents → Data Perception Layer
-- Source: https://www.kaggle.com/datasets/sobhanmoosavi/us-accidents
-- Purpose: 7.7M traffic incidents with GPS coords for route risk heatmaps
CREATE TABLE IF NOT EXISTS HYPERLOGISTICS_DB.BRONZE.TRAFFIC_INCIDENTS (
    ACCIDENT_ID STRING,
    START_TIME TIMESTAMP,
    END_TIME TIMESTAMP,
    START_LAT FLOAT,
    START_LNG FLOAT,
    END_LAT FLOAT,
    END_LNG FLOAT,
    DISTANCE FLOAT,
    DESCRIPTION STRING,
    NUMBER STRING,
    STREET STRING,
    SIDE STRING,
    CITY STRING,
    COUNTY STRING,
    STATE STRING,
    ZIPCODE STRING,
    COUNTRY STRING,
    TIMEZONE STRING,
    AIRPORT_CODE STRING,
    WEATHER_CONDITION STRING,
    TEMPERATURE NUMBER,
    HUMIDITY NUMBER,
    VISIBILITY NUMBER,
    WIND_SPEED NUMBER,
    PRECIPITATION NUMBER,
    SEVERITY NUMBER,
    TURNING_LOOP STRING,
    TRAFFIC_SIGNAL STRING,
    RAILWAY STRING,
    CROSSING STRING,
    JUNCTION STRING,
    NO_EXIT STRING,
    BUMP STRING,
    DITCH STRING,
    STOP_SIGN STRING,
    GIVE_WAY STRING,
    TRAFFIC_CALMING STRING,
    TUNNEL STRING,
    STATION STRING,
    AMENITY STRING,
    SUNRISE_SUNSET STRING,
    CIVIL_TWILIGHT STRING,
    NAUTICAL_TWILIGHT STRING,
    ASTRONOMICAL_TWILIGHT STRING
);

-- [Core #2] NOAA GSOD Weather → Intelligence & Forecasting Layer
-- Source: https://registry.opendata.aws/noaa-gsod/
-- Purpose: Weather disruption signals (icing, flooding, visibility)
-- Note: Created as an EXTERNAL TABLE in 01_setup_noaa.sql, not here.
--       This placeholder documents the expected schema.

-- [Core #3] National Bridge Inventory → Validation & Safety Layer
-- Source: https://geodata.bts.gov/datasets/national-bridge-inventory/
-- Purpose: 600K+ bridges with load/clearance limits for safety veto
CREATE TABLE IF NOT EXISTS HYPERLOGISTICS_DB.BRONZE.BRIDGE_INVENTORY (
    BRIDGE_ID STRING,
    BRIDGE_NAME STRING,
    LATITUDE FLOAT,
    LONGITUDE FLOAT,
    STATE STRING,
    COUNTY STRING,
    YEAR_BUILT NUMBER,
    YEAR_RECONSTRUCTED NUMBER,
    DECK_AREA NUMBER,
    APPROACH_WIDTH NUMBER,
    LANES NUMBER,
    STRUCTURE_LENGTH_MT NUMBER,
    MAIN_SPAN_LENGTH_MT NUMBER,
    DECK_WIDTH_MT NUMBER,
    VERTICAL_CLEARANCE_MT NUMBER,
    LOAD_LIMIT_TONS NUMBER,
    CONDITION STRING,
    STRUCTURAL_EVALUATION NUMBER,
    FUNCTIONAL_OBSOLESCENCE NUMBER
);

-- ═══════════════════════════════════════════════════════════════
-- SUPPORTING TABLES
-- ═══════════════════════════════════════════════════════════════

-- [Supporting] DataCo Supply Chain → SRSNet Training Only
-- Source: https://www.kaggle.com/datasets/shashwatwork/dataco-smart-supply-chain-for-big-data-analysis
-- Purpose: Historical delay patterns for SRSNet forecasting model training.
--          NOT used for middle-mile routing directly (lacks geographic granularity).
CREATE TABLE IF NOT EXISTS HYPERLOGISTICS_DB.BRONZE.RAW_LOGISTICS (
    ORDER_ID STRING,
    ORDER_DATE DATE,
    SHIPPING_DATE DATE,
    DELIVERY_DATE DATE,
    SHIPPING_MODE STRING,
    LATE_DELIVERY_RISK NUMBER,
    SALES_PER_CUSTOMER NUMBER,
    PROFIT_PER_ORDER NUMBER,
    CUSTOMER_ID STRING,
    CUSTOMER_SEGMENT STRING,
    PRODUCT_ID STRING,
    PRODUCT_NAME STRING,
    PRODUCT_CATEGORY STRING,
    PRODUCT_PRICE NUMBER,
    ORDER_QUANTITY NUMBER,
    PRODUCT_STATUS STRING
);

-- [Supporting] Logistics Operations Database → RAG Chatbot Knowledge Base
-- Source: https://www.kaggle.com/datasets/yogape/logistics-operations-database
-- Purpose: 85K+ records of trucking operations (loads, trips, drivers, fuel, maintenance, safety).
--          Vectorized for the RAG chatbot to answer NL queries about carrier performance & lead times.
--          NOT used for middle-mile routing directly.
CREATE TABLE IF NOT EXISTS HYPERLOGISTICS_DB.BRONZE.LOGISTICS (
    RECORD_ID STRING,
    RECORD_TYPE STRING,           -- 'load', 'trip', 'driver', 'truck', 'fuel', 'maintenance', 'safety', 'delivery'
    LOAD_ID STRING,
    TRIP_ID STRING,
    DRIVER_ID STRING,
    TRUCK_ID STRING,
    TRAILER_ID STRING,
    CUSTOMER_ID STRING,
    FACILITY_ID STRING,
    ROUTE_ID STRING,
    ORIGIN_CITY STRING,
    DESTINATION_CITY STRING,
    DISTANCE_MILES FLOAT,
    REVENUE NUMBER,
    COST NUMBER,
    FUEL_GALLONS FLOAT,
    FUEL_COST NUMBER,
    MAINTENANCE_TYPE STRING,
    MAINTENANCE_COST NUMBER,
    DELIVERY_STATUS STRING,
    ON_TIME_FLAG BOOLEAN,
    DETENTION_MINUTES NUMBER,
    SAFETY_INCIDENT_TYPE STRING,
    BOOKING_TYPE STRING,
    EVENT_DATE DATE,
    EVENT_TIMESTAMP TIMESTAMP,
    DESCRIPTION STRING,
    _INGESTED_AT TIMESTAMP
);


-- 4. Create Silver Layer Tables (Cleaned/Enriched Data)

-- ═══════════════════════════════════════════════════════════════
-- CORE MIDDLE-MILE SILVER TABLES
-- ═══════════════════════════════════════════════════════════════

-- [Core #1 Silver] US Accidents → Risk Heatmap (aggregated by location/time)
-- Produced by: src/preprocessing/preprocess_accidents.py

CREATE TABLE IF NOT EXISTS HYPERLOGISTICS_DB.SILVER.RISK_HEATMAP (
    STATE STRING,
    CITY STRING,
    HOUR TIMESTAMP,
    INCIDENT_COUNT NUMBER,
    AVG_SEVERITY FLOAT,
    _UPDATED_AT TIMESTAMP
);

-- [Core #2 Silver] NOAA Weather → Semantic weather alerts
-- Produced by: src/preprocessing/preprocess_weather.py

CREATE TABLE IF NOT EXISTS HYPERLOGISTICS_DB.SILVER.WEATHER_ALERTS (
    STATION STRING,
    DATE DATE,
    WEATHER_ALERT STRING,
    ALERT_DESCRIPTION STRING,
    PRCP FLOAT,
    SNWD FLOAT,
    VISIB FLOAT,
    _CREATED_AT TIMESTAMP
);

-- [Core #3 Silver] Bridge Inventory → GEOGRAPHY-enabled for spatial joins
-- Produced by: src/preprocessing/preprocess_bridges.py

CREATE TABLE IF NOT EXISTS HYPERLOGISTICS_DB.SILVER.BRIDGE_INVENTORY_GEO (
    BRIDGE_ID STRING,
    BRIDGE_NAME STRING,
    LOCATION GEOGRAPHY,
    STATE STRING,
    VERTICAL_CLEARANCE_MT NUMBER,
    LOAD_LIMIT_TONS NUMBER,
    _PROCESSED_AT TIMESTAMP
);

-- ═══════════════════════════════════════════════════════════════
-- SUPPORTING SILVER TABLES
-- ═══════════════════════════════════════════════════════════════

-- [Supporting Silver] DataCo → Cleaned logistics for SRSNet training
-- Produced by: src/preprocessing/preprocess_dataco.py
CREATE TABLE IF NOT EXISTS HYPERLOGISTICS_DB.SILVER.CLEANED_LOGISTICS (
    ORDER_ID STRING,
    ORDER_DATE DATE,
    SHIPPING_DATE DATE,
    DELIVERY_DATE DATE,
    SHIPPING_MODE STRING,
    LATE_DELIVERY_RISK NUMBER,
    DELAY_DAYS NUMBER,
    DELAY_PROPENSITY NUMBER,
    _INSERTED_AT TIMESTAMP
);

-- [Supporting Silver] Logistics Ops → Vectorized chunks for RAG chatbot
-- Produced by: src/preprocessing/preprocess_logistics.py
CREATE TABLE IF NOT EXISTS HYPERLOGISTICS_DB.SILVER.LOGISTICS_VECTORIZED (
    CHUNK_ID STRING,
    RECORD_TYPE STRING,              -- Source record type (load, trip, driver, etc.)
    TEXT_CONTENT STRING,             -- Human-readable text chunk for embedding
    METADATA VARIANT,                -- JSON metadata (route, driver, dates, etc.)
    EMBEDDING VECTOR(768),           -- Cortex embedding for retrieval
    SOURCE_RECORD_IDS ARRAY,         -- Original record IDs that contributed to this chunk
    _VECTORIZED_AT TIMESTAMP
);

-- 5. Create Gold Layer Tables (Analytics-Ready)

CREATE TABLE IF NOT EXISTS HYPERLOGISTICS_DB.GOLD.VECTOR_EMBEDDINGS (
    EMBEDDING_ID STRING,
    CONTENT STRING,
    EMBEDDING VECTOR(768),
    EMBEDDING_TYPE STRING,
    SOURCE_TABLE STRING,
    CREATED_AT TIMESTAMP
);

CREATE TABLE IF NOT EXISTS HYPERLOGISTICS_DB.GOLD.DISRUPTION_REPORTS (
    REPORT_ID STRING,
    DISRUPTION_TYPE STRING,
    LOCATION GEOGRAPHY,
    IMPACT_SCORE NUMBER,
    AFFECTED_ROUTES STRING,
    RECOVERY_TIME NUMBER,
    NOTES STRING,
    CREATED_AT TIMESTAMP
);

CREATE TABLE IF NOT EXISTS HYPERLOGISTICS_DB.GOLD.QUERY_LOGS (
    QUERY_ID STRING,
    USER_ID STRING,
    QUERY_TEXT STRING,
    RESPONSE_TEXT STRING,
    GROUNDING_SOURCES ARRAY,
    EXECUTION_TIME_MS NUMBER,
    IS_GROUNDED BOOLEAN,
    CREATED_AT TIMESTAMP
);

-- 6. Grant Permissions
GRANT ALL PRIVILEGES ON DATABASE HYPERLOGISTICS_DB TO ROLE SYSADMIN;
GRANT ALL PRIVILEGES ON SCHEMA HYPERLOGISTICS_DB.BRONZE TO ROLE SYSADMIN;
GRANT ALL PRIVILEGES ON SCHEMA HYPERLOGISTICS_DB.SILVER TO ROLE SYSADMIN;
GRANT ALL PRIVILEGES ON SCHEMA HYPERLOGISTICS_DB.GOLD TO ROLE SYSADMIN;

-- Grant table permissions
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA HYPERLOGISTICS_DB.BRONZE TO ROLE SYSADMIN;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA HYPERLOGISTICS_DB.SILVER TO ROLE SYSADMIN;
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA HYPERLOGISTICS_DB.GOLD TO ROLE SYSADMIN;

-- Verify setup
SELECT CURRENT_DATABASE() as current_db, COUNT(*) as table_count
FROM INFORMATION_SCHEMA.TABLES
WHERE TABLE_SCHEMA IN ('BRONZE', 'SILVER', 'GOLD')
GROUP BY CURRENT_DATABASE();