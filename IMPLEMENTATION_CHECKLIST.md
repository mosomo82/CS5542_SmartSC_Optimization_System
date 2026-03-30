# ⭐ Implementation Checklist

Follow this checklist to deploy the HyperLogistics system end-to-end.

### 1. Prerequisites
- [ ] Python 3.10+ installed
- [ ] Snowflake account (with `ACCOUNTADMIN` rights)
- [ ] AWS account (for S3 storage, if using automation)
- [ ] `.env` file configured from `.env.template`

### 2. Snowflake Environment Setup
- [ ] Run `src/sql/00_create_database.sql` (Creates DB/Schemas)
- [ ] Run `src/sql/01_setup_noaa.sql` (Creates NOAA external table)
- [ ] Run `src/sql/02_setup_s3_automation.sql` (Creates S3 stages and pipes)

### 3. Data Ingestion
- [ ] Option A (Manual): Run `python src/ingestion/ingest_accidents.py` and others.
- [ ] Option B (Automated): Run `python src/run_pipeline.py` to trigger S3/Snowpipe.

### 4. Application Deployment
- [ ] Install dependencies: `pip install -r requirements.txt`
- [ ] Launch Dashboard: `streamlit run src/app/dashboard.py`

### 5. Verification
- [ ] Run evaluation: `python tests/evaluate_system.py`
- [ ] Confirm 9-tab analytics are rendering live Snowflake data.
