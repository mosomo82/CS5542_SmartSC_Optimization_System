# Detailed Documentation for HyperLogistics: Smart Supply Chain Optimization System

## 1. Dataset & Knowledge Base Documentation

### Dataset Names, Modalities, Source Links
The system utilizes four primary datasets to build a multimodal knowledge base for middle-mile logistics optimization. These datasets cover historical logistics performance, real-time disruptions, environmental signals, and infrastructure constraints.

1. **DataCo Smart Supply Chain Dataset**
   - **Modality**: Tabular (CSV)
   - **Source Link**: [DataCo Smart Supply Chain for Big Data Analysis](https://www.kaggle.com/datasets/shashwatwork/dataco-smart-supply-chain-for-big-data-analysis)
   - **Size**: 180,000+ rows
   - **Key Fields**: Order ID, delivery dates, shipping modes, late delivery risk, customer demographics
   - **Format**: Structured CSV with timestamps and categorical data

2. **US Accidents (2016-2023)**
   - **Modality**: Geospatial Tabular (CSV)
   - **Source Link**: [US Traffic Accidents Dataset](https://www.kaggle.com/datasets/sobhanmoosavi/us-accidents)
   - **Size**: 7.7 million records (3.06 GB)
   - **Key Fields**: GPS coordinates (latitude/longitude), start/end times, severity (1-4), weather conditions, proximity to points of interest
   - **Format**: CSV with geospatial and temporal data

3. **NOAA Global Surface Summary of the Day (GSOD)**
   - **Modality**: Time-Series Geospatial (Parquet/CSV)
   - **Source Link**: [NOAA GSOD on AWS Open Data](https://registry.opendata.aws/noaa-gsod/)
   - **Size**: Multi-terabyte (daily updates)
   - **Key Fields**: Station ID, date, temperature, precipitation, wind speed, visibility
   - **Format**: Parquet files in S3 bucket, accessible via external tables

4. **National Tunnel & Bridge Inventory (US DOT)**
   - **Modality**: Geospatial Tabular (GeoJSON/CSV)
   - **Source Link**: [National Bridge Inventory](https://geodata.bts.gov/datasets/national-bridge-inventory/)
   - **Size**: 600,000+ records
   - **Key Fields**: Bridge ID, location (lat/lon), load limits, vertical clearances, structure type
   - **Format**: CSV/GeoJSON with GEOGRAPHY-compatible data

### Domain Relevance
These datasets are selected for their direct relevance to middle-mile logistics disruptions:
- **DataCo**: Provides ground truth for training predictive models on historical delays, enabling pattern recognition in supply chain operations.
- **US Accidents**: Maps real-time and historical traffic incidents to identify "blackspots" and risk propagation across routes.
- **NOAA GSOD**: Supplies environmental disruption signals (e.g., weather events) that trigger rerouting decisions, integrated as real-time feeds.
- **Bridge Inventory**: Enforces safety constraints by validating routes against physical infrastructure limits, preventing violations like bridge strikes.

Together, they form a multimodal knowledge base: tabular for logistics metrics, geospatial for location-based risks, and time-series for predictive forecasting.

### Multimodal Ingestion Details
Ingestion follows a hybrid strategy to handle scale and real-time needs:
- **Snowpipe & Streams**: For real-time data (US Accidents, NOAA GSOD). Snowpipe auto-ingests new files from S3 stages, with Streams enabling change data capture (CDC) for incremental updates.
- **Internal Stages**: For historical datasets (DataCo, Bridge Inventory). Files are uploaded to Snowflake stages (e.g., `@LOGISTICS_STAGE`) and loaded via `COPY INTO` commands.
- **External Tables**: For massive datasets (NOAA GSOD). Directly query S3 buckets without copying data, minimizing storage costs while allowing high-performance access.
- **Snowpark Python SDK**: Used for programmatic ingestion, including chunking large files (e.g., US Accidents via `snowflake-ingest` SDK).

All ingestion is orchestrated within Snowflake's Medallion Architecture: Bronze (raw landing), Silver (cleaned/standardized), Gold (analytics-ready).

### Data Preprocessing and Sampling Strategy
Preprocessing transforms raw data into analytics-ready formats using Snowpark Python and SQL:
- **DataCo**: Feature engineering calculates "Delay Propensity" scores (e.g., average delay by route/season). Sampling: Stratified by shipping mode to balance classes.
- **US Accidents**: Clustering on `Start_Time` and `State` for efficient querying. Creates a "Risk Heatmap" view aggregating incidents by location/time.
- **NOAA GSOD**: Extracts semantic "weather alerts" (e.g., "severe snow" flags) using Cortex functions. Sampling: Partitioned by date/geospatial coordinates for real-time patches.
- **Bridge Inventory**: Converts lat/lon to Snowflake `GEOGRAPHY` type for spatial joins. No sampling; full dataset retained for compliance checks.
- **General Strategy**: Outlier removal (e.g., invalid GPS), normalization (e.g., timestamps to UTC), and versioning via Dynamic Tables for freshness.

## 2. Retrieval & Processing Pipeline

### Chunking Strategy
- **Time-Series Chunking**: For forecasting (SRSNet), data is adaptively "patched" into segments (e.g., 4-8 hour windows) based on disruption signals. Patches are selected to capture relevant patterns, reducing noise from irrelevant historical data.
- **Text/Document Chunking**: For RAG, historical reports (e.g., weather impact summaries) are chunked into 512-1024 token segments using sliding windows to preserve context.
- **Geospatial Chunking**: Routes are divided into "patches" (e.g., 10-mile segments) for localized risk assessment.

### Indexing and Retrieval Configuration
- **Indexing**: Uses Snowflake's native `VECTOR` data type for embeddings. Historical disruption reports are vectorized and stored in a `VECTOR_EMBEDDINGS` table with L2 distance indexing.
- **Retrieval Configuration**: Configured via Snowflake Cortex Search. Retrieval uses `VECTOR_L2_DISTANCE` for similarity search, filtered by metadata (e.g., date, location). ReMindRAG guides traversal by prioritizing high-relevance nodes in the knowledge graph.
- **Pipeline Flow**: Query → Embed → Search Vectors → Retrieve Chunks → Generate Response.

### Embedding Models Used
- **Primary Model**: Snowflake Cortex (Google Gemini) for generating embeddings and inference. Embeddings are 768-dimensional vectors optimized for logistics metadata.
- **Fallback/Comparison**: Open-source alternatives (e.g., Sentence Transformers) if needed, but Cortex is preferred for on-platform security.

### Example Retrieval Outputs for ≥2 Project Queries
1. **Query: "Suggest reroute for shipment from Chicago to Kansas City due to severe weather."**
   - **Retrieval Output**: Retrieves chunks from NOAA GSOD (e.g., "2022 snow event on I-70 reduced visibility to 0.5 miles, causing 3-hour delays"). SRSNet patches predict 85% icing probability. Output: "Reroute via I-55 to avoid icing risk, grounded in historical data."
   
2. **Query: "Check route safety for heavy load on I-80 near Omaha."**
   - **Retrieval Output**: Retrieves from Bridge Inventory (e.g., "Bridge #12345 has 10-ton limit, violated in 15% of past incidents"). US Accidents data shows blackspots. Output: "Veto reroute; bridge clearance insufficient, based on DOT records."

### Preprocessing Scripts or Notebooks
Preprocessing scripts are included in the repository under `src/preprocessing/`. Key files:
- `preprocess_dataco.py`: Feature engineering for DataCo dataset.
- `preprocess_accidents.py`: Risk heatmap generation.
- `preprocess_weather.py`: Semantic alert extraction from NOAA.
- `preprocess_bridges.py`: Geography conversion for bridges.
- Notebooks: `notebooks/srsnet_training.ipynb` for model training.

## 3. Application Integration

### Streamlit Project Interface
The application is built with Streamlit hosted in Snowflake for low-latency access. Key components:
- **Dashboard Layout**: Interactive map (via Folium) showing routes, risk overlays, and weather heatmaps.
- **Natural Language Interface**: "Ask the Agent" sidebar using Cortex for query processing.
- **Route Comparison Tool**: Side-by-side views of original vs. AI-suggested routes with metrics (e.g., delay reduction, safety score).

### Evidence Display and Grounded Answer Generation
- **Evidence Display**: Each recommendation includes a "Reasoning Path" panel citing sources (e.g., "Based on NOAA data from 2022, rerouting reduces delay by 20%").
- **Grounded Generation**: Answers are generated via ReMindRAG, ensuring outputs reference specific historical data. Neuro-symbolic layer (CPP) validates against symbolic rules.

### Query Logging or Evaluation Outputs
- **Logging**: All queries and responses are logged to a Snowflake Event Table (`QUERY_LOGS`) with timestamps, user ID, and outcomes for auditability.
- **Evaluation Outputs**: Synthetic "Golden Dataset" (50 scenarios) evaluates accuracy. Outputs include precision metrics (e.g., 90% grounding accuracy).

### Screenshots or Deployment Link
- Screenshots: Include `docs/screenshots/dashboard_overview.png` and `docs/screenshots/reroute_comparison.png`.
- Deployment Link: Hosted at `https://<snowflake_account>.snowflakecomputing.com/streamlit/apps/HYPERLOGISTICS_APP` (replace with actual).

## 4. Snowflake Data Pipeline & Schema

### Snowflake Schema (Tables, Stages, Views)
- **Stages**: `@LOGISTICS_STAGE`, `@ACCIDENTS_STAGE`, `@NOAA_S3_STAGE` (external), `@BRIDGE_STAGE`, `@APP_STAGE`.
- **Tables**:
  - Bronze: `RAW_LOGISTICS` (DataCo), `TRAFFIC_INCIDENTS` (US Accidents), `NOAA_GSOD` (external).
  - Silver: `CLEANED_LOGISTICS`, `RISK_HEATMAP`.
  - Gold: `VECTOR_EMBEDDINGS`, `DISRUPTION_REPORTS`.
- **Views**: `RISK_HEATMAP_VIEW` (aggregated accidents), `WEATHER_ALERTS_VIEW` (semantic NOAA).

### Reproducible Ingestion Scripts (SQL / Snowpark / Python)
Scripts in `src/ingestion/`:
- `ingest_dataco.py`: Snowpark script for DataCo loading.
- `ingest_accidents.py`: Python for chunked upload.
- `ingest_bridges.py`: Geography conversion.
- `01_setup_noaa.sql`: SQL for external table.
- `ingest_bridges.py`: Geography conversion.

### Example Queries Demonstrating Warehouse Connectivity
- **Connectivity Test**: `SELECT COUNT(*) FROM BRONZE.RAW_LOGISTICS;`
- **Risk Query**: `SELECT * FROM SILVER.RISK_HEATMAP WHERE STATE = 'IL' AND START_TIME > '2023-01-01';`
- **Spatial Join**: `SELECT * FROM GOLD.BRIDGE_INVENTORY WHERE ST_INTERSECTS(LOCATION, ST_GEOGFROMTEXT('POINT(-87.6298 41.8781)'));`

### Description of How Snowflake Integrates with the Project Application
Snowflake serves as the unified data platform: Data is ingested/stored here, ML (SRSNet/Cortex) runs on-platform, and Streamlit apps query directly via Snowpark. This ensures security, scalability, and real-time access without data egress.

## 5. Reproducibility Plan

### Environment Configuration
- **Python**: 3.10 or 3.11.
- **Virtual Environment**: Use `venv` (see `reproducibility/README_reproducibility.md`).
- **Dependencies**: Listed in `requirements.txt` (includes Snowpark, Streamlit, scikit-learn).
- **Snowflake**: Enterprise Edition on AWS, with roles (SYSADMIN) and warehouses (COMPUTE_WH).

### Model Versions and Dataset Versioning
- **SRSNet**: Version from NeurIPS 2025 (arXiv:2510.14510), pinned to commit `abc123` in `src/models/`.
- **ReMindRAG**: Version from arXiv:2510.13193, integrated via Cortex.
- **Datasets**: Versioned by source (e.g., DataCo v1.0 from Kaggle), with checksums in `data/checksums.txt`.

### Random Seeds and Configuration Files
- **Seeds**: Set in `config.yaml` (e.g., `random_seed: 42` for SRSNet training).
- **Configs**: `src/config/config.yaml` includes hyperparameters, API keys (via `.env`), and dataset paths.

### Run Instructions
Follow the step-by-step guide in `reproducibility/README_reproducibility.md`:
1. Clone repo and set up venv.
2. Configure `.env` for Snowflake.
3. Ingest data via scripts.
4. Train models and deploy Cortex.
5. Launch Streamlit app.
6. Evaluate with `tests/evaluate_system.py`.