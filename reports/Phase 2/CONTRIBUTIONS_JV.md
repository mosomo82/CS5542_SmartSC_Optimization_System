# Individual Contribution Statement: Joel Vinas

**GitHub Aliases:** `jvinas` / `joelvinas`

## Role
**Internal Data Engineering Lead**

## Contribution Description
- **Database Design & Schema Creation:** Designed and configured the core internal Snowflake database environment (`SMART_SUPPLY_CHAIN_DB`), including all required schemas and table definitions to house the project's operational datasets (`src/sql/00_create_database.sql`).
- **Manual Data Ingestion:** Authored all internal ingestion scripts responsible for loading raw source data into Snowflake's bronze layer. This included dedicated pipelines for the DataCo supply chain, logistics, accidents, and bridges datasets (`src/ingestion/ingest_dataco.py`, `src/ingestion/ingest_logistics.py`, `src/ingestion/ingest_accidents.py`, `src/ingestion/ingest_bridges.py`).
- **Silver-Layer Preprocessing:** Developed the preprocessing modules that clean, transform, and promote raw ingested data into the silver-level analytical layer, ensuring data quality and consistency for downstream consumption (`src/preprocessing/preprocess_dataco.py`, `src/preprocessing/preprocess_logistics.py`, `src/preprocessing/preprocess_accidents.py`, `src/preprocessing/preprocess_bridges.py`).
- **Dataset Documentation:** Documented the use of the DataCo Supply Chain dataset, capturing source provenance, field definitions, and licensing context to support reproducibility and transparency.
- **Project Infrastructure:** Contributed structural and architecture updates to the repository, including establishing the `.gitignore` configuration for dependency and artifact management, and refining the Reproducibility Guide introduction.

## Contribution Percentage
**33%**

## Evidence (Commits & Implementations)
- **Commits:** `a0df45c` (Document DataCo Supply Chain dataset usage), `890c77c` (Update Reproducibility Guide introduction), `62fc914` (Add .gitignore for project dependencies and artifacts), `187ec1a` (Structural and architecture updates).
- **Core Files Delivered:**
  - `src/sql/00_create_database.sql`
  - `src/ingestion/ingest_dataco.py`
  - `src/ingestion/ingest_logistics.py`
  - `src/ingestion/ingest_accidents.py`
  - `src/ingestion/ingest_bridges.py`
  - `src/preprocessing/preprocess_dataco.py`
  - `src/preprocessing/preprocess_logistics.py`
  - `src/preprocessing/preprocess_accidents.py`
  - `src/preprocessing/preprocess_bridges.py`

---

## 📈 Individual Contribution Statement Summary

*The following outlines the precise contribution margins ensuring a 100% totality across all technical project categories (code, pipeline, deployment, evaluation, documentation).*

| Member | Contribution Description | Contribution % | Primary Evidence Link |
|--------|--------------------------|----------------|-----------------------|
| **Joel Vinas** | Built internal database infrastructure, performed native SQL schema creation, managed manual ingestion loops, and documented base reproducibility setups. Included detailed breakdown in [`CONTRIBUTIONS_JV.md`](CONTRIBUTIONS_JV.md). | **33%** | Commits: `a0df45c`, `890c77c`, `187ec1a` / Files: `00_create_database.sql`, `ingest_*.py` |
| **Daniel Evans** | Integrated external NOAA APIs, developed silver-layer weather data transformations, and deployed the comprehensive Streamlit interactive dashboard. | **33%** | PR #1: `daniel-phase2` / Files: `dashboard.py`, `01_setup_noaa.sql` |
| **Tony Nguyen** | Engineered the end-to-end automation pipelines, S3-to-Snowflake integrations, verification tests, and defined the project architecture/reproducibility guides. | **34%** | Commits: `d0e0ec7`, `673d815`, `22d4928` / Files: `run_pipeline.py`, `setup_s3_automation.py` |
