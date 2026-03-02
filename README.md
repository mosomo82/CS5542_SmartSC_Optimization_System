# HyperLogistics: Smart Supply Chain Optimization System

**A Snowflake-Native Supply Chain Resilience System using RAG**

| **Team Members** | **GitHub Role** |
| --- | --- |
| **Daniel Evans** | [`@devans2718`](https://github.com/devans2718)  Data/Back-End Engineer |
| **Joel Vinas** | [`@joelvinas`](https://github.com/joelvinas) Data Engineer/ML Engineer |
| **Tony Nguyen** | [`@mosomo82`](https://github.com/mosomo82) ML/Full-Stack Engineer |

---

## 🎯 Problem Statement & Objectives

**The Problem:** Middle-mile logistics suffer from a 'prediction-action' gap where managers lack tools to instantly calculate safe alternatives during real-time disruptions like weather or accidents

**The Objective:** Build a neuro-symbolic engine that generates autonomously validated rerouting strategies grounded in safety and compliance.
* **Innovation:**  We utilize ReMindRAG for knowledge-guided retrieval and SRSNet for adaptive time-series forecasting.
* **Target Users:** Logistics Network Managers and Area Managers.

---

## 🏗️ System Architecture Diagram
The **HyperLogistics** engine utilizes a Snowflake-native ecosystem to bridge the "prediction-action" gap through four specialized layers: 
### **1. Data Perception Layer**
* **Ingestion:** Manages hybrid ingestion via **Snowpipe** (real-time NOAA weather/US DOT bridge data) and **Internal Stages** (historical DataCo logistics/US Accidents).
* **Storage:** Organizes data into a **Medallion Architecture** (Bronze, Silver, Gold) to ensure all inputs are analytics-ready.
### **2. Intelligence & Forecasting Layer**
* **Reasoning Agent:** Employs **ReMindRAG** for LLM-guided knowledge graph traversal, grounding AI reasoning in historical disruption metadata.
* **Predictive Analyst:** Uses **SRSNet** via Snowpark Python to predict risk propagation across middle-mile "patches" over 4–8 hour windows.
* **Inference:** Leverages **Snowflake Cortex** (Google Gemini) for secure, on-platform generative reasoning.
### **3. Validation & Safety Layer (Neuro-Symbolic)**
* **Planning Agent:** Implements the **Consensus Planning Protocol (CPP)** where specialized agents negotiate the optimal route.
* **Safety Veto:** A symbolic guardrail that runs **Spatial SQL joins** against the **DOT Bridge Inventory** to enforce 100% compliance with physical clearances.
### **4. Application Layer**
* **Dispatcher Dashboard:** A **Streamlit in Snowflake** application featuring interactive risk heatmaps and natural language "Ask the Agent" queries.
* **Decision Support:** Provides side-by-side route comparisons with explainable justifications to eliminate the "lack of trust" bottleneck.

![Architecture Diagram](./docs/Figures/architecture2.png)

## 🛠️ Methods & Technologies

### **Methods & Technologies**

| **Component** | **Tool** | **Implementation Detail** |
| --- | --- | --- |
| **Development Environment** | **Google Colab** | Serves as the primary client-side environment for orchestrating Snowpark pipelines. |
| **Data Engine** | **Snowflake** | Core platform for ingestion (Snowpipe), storage (Medallion Architecture), and processing (Snowpark). |
| **Graph Intelligence** | **NetworkX on SNowpark** | Executes hypergraph logic natively inside Snowflake to model complex supply chain ripple effects. |
| **Inference Engine** | **Snowflake Cortex** | Leverages Google Gemini for secure LLM reasoning directly beside the data. |
| **RAG Architecture** | **ReMindRAG** | Uses LLM-guided knowledge graph traversal to provide low-cost, explainable justifications for rerouting. |
| **Forecasting** | **SRSNet** | Implements "Selective Representation" to patch time-series data for weather and accident propagation. |
| **Safety Protocol** | **Consensus Planning (CPP)** | A multi-agent system where Context, Efficiency, and Compliance agents must negotiate a final route. |
| **Safety Veto** | **Spatial SQL** | Hard-coded guardrail cross-referencing routes against **US DOT Bridge Inventory** using `GEOGRAPHY` types. |
| **Frontend** | **Streamlit in Snowflake** | Interactive dashboard for real-time risk visualization and natural language interaction |
---

## 📚 Data Sources & References

### **NeurIPS 2025 Reasearch Papers (with Code)**

1. **Enhancing Time Series Forecasting through Selective Representation Spaces (SRSNet)**
* **Link:** [https://arxiv.org/abs/2510.14510](https://arxiv.org/abs/2510.14510)
* **Summary:** Proposes a technique that adaptively selects "patches" of data to improve long-term pattern detection.
* **Project Integration:** We adopt the **SRS philosophy** to enable our Snowflake-native models to remain flexible with real-time telematics and longer-term weather forecasts.

2. **ReMindRAG: Low-Cost LLM-Guided Knowledge Graph Traversal for Efficient RAG**
* **Link:** [https://arxiv.org/abs/2510.13193](https://arxiv.org/abs/2510.13193)
* **Summary:** Introduces a method for LLM-guided graph traversal that reduces token usage while retaining accuracy.
* **Project Integration:** Used to search fragmented data sources and provide dispatchers with high-quality, explainable justifications for rerouting, solving the "explainability gap".

3. **Consensus Planning with Primal, Dual, and Proximal Agents (CPP)**
* **Link:** [https://www.amazon.science/publications/consensus-planning-with-primal-dual-and-proximal-agents](https://www.amazon.science/publications/consensus-planning-with-primal-dual-and-proximal-agents)
* **Summary:** Defines a protocol where different supply chain agents negotiate to agree on a single optimal plan.
* **Project Integration:** Our architecture uses a **Validation Agent** to negotiate between the LLM's suggested route and physical constraints (bridge height/weight) before rendering the final recommendation.



### **Core Middle-Mile Datasets**

The following three datasets form the core of the middle-mile rerouting engine. Each is **geospatially grounded** with GPS coordinates, enabling overlay on actual freight corridors.

1. **US Accidents (2016 - 2023)** — *Route-Level Disruption Risk*
   * **Link:** [US Traffic Accidents](https://www.kaggle.com/datasets/sobhanmoosavi/us-accidents) 
   * **Description:** A countrywide dataset of 7.7 million traffic incident records with precise GPS coordinates, severity ratings, and road feature annotations.
   * **Middle-Mile Role:** Maps directly to the **Data Perception Layer**. Ingested via Snowpark to create the `RISK_HEATMAP_VIEW`, allowing the system to cross-reference proposed routes against historical accident "blackspots" along freight corridors (I-70, I-80, I-55, etc.).
   * **Modality:** Geospatial Tabular (CSV) — 7.7M rows × 47 columns

2. **NOAA Global Surface Summary of the Day (GSOD)** — *Disruption Trigger Signals*
   * **Link:** [NOAA GSOD](https://registry.opendata.aws/noaa-gsod/) 
   * **Description:** A multi-terabyte environmental dataset providing real-time weather signals: precipitation, snowfall, visibility, wind speed, and temperature across thousands of stations.
   * **Middle-Mile Role:** Maps to the **Intelligence & Forecasting Layer**. Connected as a Snowflake External Table; Cortex functions extract semantic "weather alerts" (icing, flooding, low visibility) to justify real-time rerouting decisions. SRSNet uses this data for 4–8 hour risk propagation forecasting — the exact transit-time scale for middle-mile shipments.
   * **Modality:** Time-Series Geospatial (Parquet) — multi-terabyte

3. **National Bridge Inventory (US DOT)** — *Hard Safety Constraint*
   * **Link:** [National Bridge Inventory](https://geodata.bts.gov/datasets/national-bridge-inventory/) 
   * **Description:** Records for over 600,000 bridges including load limits, vertical clearances, structural evaluations, and precise GPS locations.
   * **Middle-Mile Role:** Maps to the **Validation & Safety Layer**. Acts as the "Hard-Veto" guardrail — Spatial SQL joins cross-reference every suggested re-route against bridge `VERTICAL_CLEARANCE_MT` and `LOAD_LIMIT_TONS` to enforce 100% compliance with physical constraints. A route is automatically rejected if any bridge along the path violates vehicle clearance limits.
   * **Modality:** Geospatial Tabular (CSV/GeoJSON) — 600K+ records

### **Supporting Datasets**

4. **DataCo Smart Supply Chain (Kaggle)** — *Historical Pattern Training*
   * **Link:** [DataCo Smart Supply Chain](https://www.kaggle.com/datasets/shashwatwork/dataco-smart-supply-chain-for-big-data-analysis) 
   * **Description:** 180k+ rows of structured logistics data, including delivery times and shipping modes.
   * **Supporting Role:** Provides `shipping_mode`, `delay_days`, and `late_delivery_risk` features for SRSNet historical pattern training. Not used for middle-mile routing directly (lacks route-level geographic granularity).

5. **Logistics Operations Database (Kaggle)** — *RAG Knowledge Base*
   * **Link:** [Logistics Operations Database](https://www.kaggle.com/datasets/yogape/logistics-operations-database)
   * **Description:** 85K+ records across 14 interconnected tables from a 3-year Class 8 trucking operation (2022–2024). Covers loads, trips, drivers, trucks, fuel purchases, maintenance records, delivery events, and safety incidents.
   * **Supporting Role:** Vectorized into `SILVER.LOGISTICS_VECTORIZED` for the RAG chatbot to answer natural language queries about carrier performance, lead times, route profitability, and maintenance history. Not used for route-level disruption analysis.
   * **Scripts:** `src/ingestion/ingest_logistics.py` → `src/preprocessing/preprocess_logistics.py`
---

## 📂 Repository Structure

```text
/Project_SmartSC_Optimization_System
├── data/                 # Dataset files (CSV, JSON) for ingestion
├── docs/                 # System diagrams, design notes, and meeting logs
├── proposal/             # Your formal PDF proposal and research drafts
├── reproducibility/      # Guides or scripts specifically for reproducing results
├── src/                  # Source code for ingestion, graph building, and the app
└── README.md             # The main project landing page
```

---

## 📊 Dataset & Knowledge Base Documentation

### Dataset Names, Modalities, and Source Links
The system focuses on **three core middle-mile datasets** that are geospatially grounded and map directly to the architecture's three functional layers:

| # | Dataset | Modality | Source | Size | Architecture Layer |
|---|---------|----------|--------|------|--------------------|
| 1 | **US Accidents (2016–2023)** | Geospatial Tabular (CSV) | [Kaggle](https://www.kaggle.com/datasets/sobhanmoosavi/us-accidents) | 7.7M records | Data Perception |
| 2 | **NOAA GSOD** | Time-Series Geospatial (Parquet) | [AWS Open Data](https://registry.opendata.aws/noaa-gsod/) | Multi-terabyte | Intelligence & Forecasting |
| 3 | **National Bridge Inventory** | Geospatial Tabular (CSV/GeoJSON) | [US DOT](https://geodata.bts.gov/datasets/national-bridge-inventory/) | 600K+ records | Validation & Safety |

### Domain Relevance to the Project
Middle-mile logistics — the transportation leg between distribution centers — requires **route-level, geospatially grounded** data for disruption detection and rerouting. The three core datasets provide orthogonal coverage of the middle-mile problem space:

- **US Accidents** → *"Where are the historical risk zones along freight corridors?"* — Enables proactive avoidance of accident blackspots.
- **NOAA Weather** → *"What real-time environmental conditions could disrupt transit?"* — Provides the disruption trigger signals (icing, flooding, low visibility) that initiate the rerouting workflow.
- **Bridge Inventory** → *"Can the vehicle physically traverse this alternate route?"* — Enforces hard physical constraints (clearance, load limits) that no AI reasoning can override.

Together, these datasets answer the three fundamental middle-mile questions: *risk, trigger*, and *feasibility*.

### Multimodal Ingestion Details

| Dataset | Ingestion Method | Bronze Table | Format |
|---------|------------------|--------------|--------|
| US Accidents | **Snowpipe** (real-time) via S3 | `BRONZE.TRAFFIC_INCIDENTS` | CSV → 47 columns (GPS, severity, road features, weather at scene) |
| NOAA GSOD | **External Table** (direct S3 access) | `BRONZE.NOAA_GSOD` | Parquet → station-level daily summaries (PRCP, SNWD, VISIB, TEMP) |
| Bridge Inventory | **Internal Stage** (batch load) | `BRONZE.BRIDGE_INVENTORY` | CSV/GeoJSON → structural attributes + lat/lon coordinates |

- **Snowpipe** provides event-driven, near-real-time ingestion for US Accidents data.
- **External Tables** avoid data duplication for the multi-terabyte NOAA archive — queries run directly against S3.
- **Internal Stages** batch-load the relatively static Bridge Inventory (~600K records, updated annually by US DOT).
- **Automated S3 Loading**: See `src/sql/02_setup_s3_automation.sql` and `src/ingestion/setup_s3_automation.py` for full automation setup.

### Data Preprocessing and Sampling Strategy

Preprocessing scripts in `src/preprocessing/` transform raw Bronze-layer data into analytics-ready Silver-layer tables:

| Dataset | Script | Key Transformations | Sampling Strategy | Silver Output |
|---------|--------|---------------------|-------------------|---------------|
| **US Accidents** | `preprocess_accidents.py` | Aggregation by State/City/Hour; severity averaging; risk scoring | **Geospatial clustering** — incidents grouped by proximity to major freight corridors (I-70, I-80, I-55, I-10) with severity weighting | `SILVER.RISK_HEATMAP_VIEW` |
| **NOAA GSOD** | `preprocess_weather.py` | Rule-based alert extraction (PRCP > 50mm, SNWD > 10cm, VISIB < 1mi); semantic description generation | **Temporal windowing** — 4–8 hour adaptive patches aligned to middle-mile transit windows for SRSNet input | `SILVER.WEATHER_ALERTS` |
| **Bridge Inventory** | `preprocess_bridges.py` | Lat/lon → Snowflake `GEOGRAPHY` type conversion via `ST_GEOGFROMTEXT`; constraint field extraction | **No sampling** — full 600K+ inventory retained for exhaustive spatial join coverage (safety-critical, cannot miss a bridge) | `SILVER.BRIDGE_INVENTORY_GEO` |

---

## 🔄 Retrieval & Processing Pipeline

### Chunking Strategy
- **Time-Series**: Adaptive patching (4-8 hour windows) for SRSNet forecasting
- **Text**: 512-1024 token segments with sliding windows
- **Geospatial**: 10-mile route segments for localized risk

### Indexing and Retrieval Configuration
- **Indexing**: Snowflake VECTOR type with L2 distance
- **Retrieval**: Cortex Search with ReMindRAG-guided traversal
- **Hybrid**: Dense/sparse retrieval with reranking

### Embedding Models Used
- **Primary**: Snowflake Cortex (Google Gemini) for 768D embeddings
- **Fallback**: Sentence Transformers for comparison

### Example Retrieval Outputs
1. **Query**: "Reroute Chicago to KC due to weather"
   - **Output**: "Reroute via I-55; NOAA shows 85% icing risk on I-70"

2. **Query**: "Heavy load safety on I-80 near Omaha"
   - **Output**: "Veto; Bridge #12345 limit violated in 15% of incidents"

### Preprocessing Scripts (Core Middle-Mile)
- `src/preprocessing/preprocess_accidents.py` — Risk heatmap aggregation
- `src/preprocessing/preprocess_weather.py` — Semantic weather alert extraction
- `src/preprocessing/preprocess_bridges.py` — GEOGRAPHY type conversion for spatial joins

---

## 🖥️ Application Integration

### Streamlit Project Interface
Interactive dashboard with risk heatmaps, natural language queries, and route comparisons.

### Evidence Display and Grounded Answer Generation
"Reasoning Path" panel cites sources; ReMindRAG ensures grounded responses.

### Query Logging and Evaluation
Logs to Snowflake Event Table; evaluated against 50-scenario golden dataset.

### Screenshots/Deployment
Live app: [https://cs5542hyperlogistics.streamlit.app/](https://cs5542hyperlogistics.streamlit.app/)

---

## ❄️ Snowflake Data Pipeline & Schema

### Schema (Tables, Stages, Views) — Core Middle-Mile
- **Stages**: `@ACCIDENTS_STAGE` (S3/Snowpipe), `@NOAA_S3_STAGE` (External), `@BRIDGES_STAGE` (S3/Snowpipe)
- **Bronze Tables**: `BRONZE.TRAFFIC_INCIDENTS`, `BRONZE.NOAA_GSOD`, `BRONZE.BRIDGE_INVENTORY`
- **Silver Tables**: `SILVER.RISK_HEATMAP`, `SILVER.WEATHER_ALERTS`, `SILVER.BRIDGE_INVENTORY_GEO`
- **Views**: `SILVER.RISK_HEATMAP_VIEW`

### Schema — Supporting Datasets
- **Stages**: `@DATACO_STAGE` (S3/Snowpipe), `@LOGISTICS_STAGE` (S3/Snowpipe)
- **Bronze Tables**: `BRONZE.RAW_LOGISTICS` (DataCo), `BRONZE.LOGISTICS` (Logistics Ops DB)
- **Silver Tables**: `SILVER.CLEANED_LOGISTICS` (DataCo), `SILVER.LOGISTICS_VECTORIZED` (RAG-ready)

### Ingestion Scripts (Core Middle-Mile)
- `src/ingestion/ingest_accidents.py` — US Accidents → `BRONZE.TRAFFIC_INCIDENTS`
- `src/sql/01_setup_noaa.sql` — NOAA GSOD External Table → `BRONZE.NOAA_GSOD`
- `src/ingestion/ingest_bridges.py` — Bridge Inventory → `BRONZE.BRIDGE_INVENTORY`

### Ingestion Scripts (Supporting)
- `src/ingestion/ingest_dataco.py` — DataCo → `BRONZE.RAW_LOGISTICS`
- `src/ingestion/ingest_logistics.py` — Logistics Ops (14 CSVs) → `BRONZE.LOGISTICS`

### Example Queries
```sql
-- Middle-mile risk: Top accident blackspots along freight corridors
SELECT STATE, CITY, INCIDENT_COUNT, AVG_SEVERITY
FROM SILVER.RISK_HEATMAP WHERE STATE = 'IL' ORDER BY INCIDENT_COUNT DESC;

-- Weather disruption triggers: Active alerts
SELECT * FROM SILVER.WEATHER_ALERTS WHERE WEATHER_ALERT != 'Normal conditions';

-- Safety veto: Bridge clearance check for a route
SELECT BRIDGE_NAME, VERTICAL_CLEARANCE_MT, LOAD_LIMIT_TONS
FROM SILVER.BRIDGE_INVENTORY_GEO
WHERE ST_DISTANCE(LOCATION, ST_GEOGFROMTEXT('POINT(-95.9 41.3)')) < 16093;  -- 10 miles
```

### Integration with Application
Snowflake as unified platform: data storage, ML inference, and Streamlit hosting.

---

## 🔁 Reproducibility Plan

### Environment Configuration
- Python 3.10+, venv, dependencies in `requirements.txt`
- Snowflake Enterprise on AWS

### Model/Dataset Versioning
- SRSNet/ReMindRAG pinned to NeurIPS versions
- Datasets versioned with checksums

### Random Seeds and Configs
- Seed: 42 in `src/config/config.yaml`
- Hyperparameters and paths configured

### Run Instructions
1. Clone repo, setup venv
2. Configure `.env`
3. Run ingestion scripts (or setup automated S3 loading)
4. Train models, deploy app
5. Evaluate with `tests/evaluate_system.py`

See `docs/detailed_documentation.md` and `docs/s3_automation_guide.md` for full details.

---

## ✅ Implementation Status

This repository now includes:
- ✅ Complete dataset documentation with sources and preprocessing
- ✅ Retrieval pipeline with chunking, indexing, and example outputs
- ✅ Streamlit application interface with dashboard components
- ✅ Snowflake schema, ingestion scripts, and SQL setup
- ✅ **Automated S3 data loading** with Snowpipe integration
- ✅ Reproducibility plan with environment config and run instructions
- ✅ All required source code files in `src/`
- ✅ Preprocessing scripts and training notebook
- ✅ Evaluation framework with golden dataset
- ✅ Dependencies in `requirements.txt`

---

## 📖 Documentation & Guides

**START HERE:** [Implementation Checklist](IMPLEMENTATION_CHECKLIST.md) ⭐

- **[Snowflake Setup Guide](docs/snowflake_setup.md)** - Database setup instructions
- **[Fix: DB Does Not Exist](docs/fix_db_not_exist.md)** - Common error & solution
- **[S3 Automation Guide](docs/s3_automation_guide.md)** - Full setup instructions
- **[S3 Quick Reference](docs/s3_quick_reference.md)** - Commands & templates
- **[Bucket Types Explained](docs/s3_bucket_types.md)** - Architecture decisions
- **[Troubleshooting: Invalid Principal](docs/troubleshoot_invalid_principal.md)** - Fix common errors
- **[Detailed Documentation](docs/detailed_documentation.md)** - All components explained

---

## 🚀 Quick Start

1. **Configure Snowflake & AWS:**
   ```bash
   cp .env.template .env
   # Fill in: SNOWFLAKE_ACCOUNT, SNOWFLAKE_USER, SNOWFLAKE_PASSWORD, S3_BUCKET
   ```

2. **Validate AWS Setup:**
   ```bash
   python src/ingestion/validate_aws_role.bat  # Windows
   # or
   ./src/ingestion/validate_aws_role.sh        # Linux/Mac
   ```

3. **Create S3 Bucket:**
   ```bash
   .\src\ingestion\create_s3_bucket.bat  # Windows
   # or
   bash src/ingestion/create_s3_bucket.sh  # Linux/Mac
   ```

4. **Apply Bucket Policy:**
   ```bash
   python src/ingestion/setup_s3_automation.py
   aws s3api put-bucket-policy --bucket YOUR_BUCKET --policy file://s3_bucket_policy.json
   ```

5. **Configure Snowflake & Upload Data:**
   
   **IMPORTANT:** Run SQL scripts in this order:
   1. `src/sql/00_create_database.sql` - Creates database, schemas & tables
   2. `src/sql/01_setup_noaa.sql` - Creates NOAA external table
   3. `src/sql/02_setup_s3_automation.sql` - Creates S3 stages & pipes
   
   Then: `python upload_to_s3.py`

**Troubleshooting?** 
- Database error? → See [docs/snowflake_setup.md](docs/snowflake_setup.md)
- Invalid principal error? → See [docs/troubleshoot_invalid_principal.md](docs/troubleshoot_invalid_principal.md)
