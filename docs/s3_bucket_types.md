# 📂 S3 Bucket Types & Architecture

HyperLogistics employs a dual-bucket strategy to balance performance and cost.

### 1. Hot Storage (Fast Ingestion)
- **Bucket:** `hyperlogistics-raw`
- **Purpose:** Ingests live weather alerts and accident feeds.
- **Config:** Standard S3 Tier for high-frequency access by Snowpipe.

### 2. Cold Storage (Historical Data)
- **Bucket:** `hyperlogistics-archive`
- **Purpose:** Stores years of historical NBI bridge data and DOT logs.
- **Config:** S3 Intelligent-Tiering to minimize costs for dormant data.

### 3. Data Lifecycle
- Automation scripts in `src/ingestion/setup_s3_automation.py` handle the transition from raw to silver.
- **Silver Tables** act as the primary queryable source for the AI Agent, reducing the need to hit S3 repeatedly.
