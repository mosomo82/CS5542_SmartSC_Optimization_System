# 🔄 HyperLogistics: Reproducibility Guide

**Version:** 1.0  
**Last Updated:** February 2026  
**Authors:** Tony Nguyen, Daniel Evans, Joel Vinas

---

## 📌 Overview
This guide details the exact steps required to instantiate the **HyperLogistics** Middle-Mile Optimization System. The architecture is **Snowflake-Native**, meaning 90% of the setup occurs within the Snowflake Data Cloud using **Snowpark Python** and **Cortex AI**.

### 🛠️ Prerequisites
* **Snowflake Account:** Enterprise Edition (or Trial) on **AWS** (required for Cortex/Iceberg compatibility).
* **Python:** Version `3.10` or `3.11` (compatible with Snowpark).
* **Kaggle Account:** To download the "Ground Truth" datasets.
* **IDE:** VS Code (recommended) or PyCharm.

---

## 🚀 Step 1: Repository & Environment Setup

### 1.1 Clone the Repository
```bash
git clone [https://github.com/mosomo82/CS5542_SmartSC_Optimization_System](https://github.com/mosomo82/CS5542_SmartSC_Optimization_System.git)
cd CS5542_SmartSC_Optimization_System

```

### 1.2 Initialize Python Environment

We use `venv` to manage Snowpark dependencies.

```bash
# Create virtual environment
python -m venv venv

# Activate (Windows)
.\venv\Scripts\activate

# Activate (Mac/Linux)
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt

```

### 1.3 Configure Secrets

**CRITICAL:** Do not push this file. Create a `.env` file in the root directory:

```ini
# .env file
SNOWFLAKE_ACCOUNT="<your_account_locator>"
SNOWFLAKE_USER="<your_username>"
SNOWFLAKE_PASSWORD="<your_password>"
SNOWFLAKE_ROLE="SYSADMIN"
SNOWFLAKE_WAREHOUSE="COMPUTE_WH"
SNOWFLAKE_DATABASE="HYPERLOGISTICS_DB"
SNOWFLAKE_SCHEMA="BRONZE"

```

---

## 💾 Step 2: Data Ingestion (The "Perception" Layer)

Because the **US Accidents** dataset (3GB+) and **NOAA Weather** (TB+) are too large for GitHub, follow these specific ingestion strategies.

### 2.1 US Accidents (Traffic Risk)

1. **Download:** [US Accidents (2016-2023)](https://www.kaggle.com/datasets/sobhanmoosavi/us-accidents) from Kaggle.
2. **Upload to Snowflake:**
* Log into Snowsight.
* Navigate to `Data` -> `Databases` -> `HYPERLOGISTICS_DB` -> `BRONZE`.
* Create Stage: `CREATE STAGE @ACCIDENTS_STAGE`.
* Upload the CSV files to the stage.


3. **Run Ingestion Script:**
```bash
python src/ingestion/ingest_accidents.py

```



### 2.2 NOAA Weather (Environmental Context)

We do *not* download this. We connect to the AWS Open Data bucket via an **External Table**.

1. Run the SQL setup script directly in Snowflake Worksheet:
```sql
-- Located in src/sql/01_setup_noaa.sql
CREATE OR REPLACE EXTERNAL TABLE BRONZE.NOAA_GSOD
LOCATION = @NOAA_S3_STAGE
FILE_FORMAT = (TYPE = PARQUET);

```



### 2.3 US DOT Bridge Inventory (Safety Veto)

1. **Download:** [National Bridge Inventory](https://www.fhwa.dot.gov/bridge/nbi.cfm).
2. **Upload:** Upload the `NBI_2024.csv` to `@BRIDGE_STAGE`.
3. **Run Spatial Conversion:**
```bash
# Converts CSV lat/lon to Snowflake GEOGRAPHY objects
python src/ingestion/ingest_bridges.py

```



### 2.4 DataCo Supply Chain (Ground Truth)
This dataset trains our SRSNet model to predict "Delay Propensity."

1.  **Download:** [DataCo Smart Supply Chain](https://www.kaggle.com/datasets/shashwatwork/dataco-smart-supply-chain-for-big-data-analysis) from Kaggle.
2.  **Upload:**
    * Rename the file to `dataco_supply_chain.csv`.
    * Upload it to the Snowflake internal stage `@DATACO_STAGE`.
3.  **Run Ingestion Script:**
    ```bash
    # Loads data into BRONZE.RAW_LOGISTICS and performs initial cleaning
    python src/ingestion/ingest_dataco.py
    ```


    
---

## 🧠 Step 3: Intelligence Layer Setup

### 3.1 Deploy Cortex Functions (Week 2)

This registers the Python UDFs that wrap the **Google Gemini** models.

```bash
python src/cortex/deploy_agents.py

```

* *Verifies:* `CORTEX.COMPLETE()` availability.
* *Creates:* `Reasoning_Agent()` function in Snowflake.

### 3.2 Train SRSNet Forecasting (Week 3)

This trains the "Selective Representation" model on the **DataCo** dataset to predict delay propensity.

```bash
python src/models/train_srsnet.py --epochs 50 --patch_size 24

```

* *Output:* Saves the trained model to the Snowflake Model Registry.

---

## 📊 Step 4: Launching the Application

### 4.1 Run Streamlit Locally (Dev Mode)

```bash
streamlit run src/app/dashboard.py

```

### 4.2 Deploy to Snowflake (Production)

1. Copy the contents of `src/app/` to your Snowflake Stage.
2. Run:
```sql
CREATE STREAMLIT HYPERLOGISTICS_APP
ROOT_LOCATION = '@APP_STAGE'
MAIN_FILE = 'dashboard.py'
QUERY_WAREHOUSE = 'COMPUTE_WH';

```



---

## ✅ Step 5: Verification (The "Golden Dataset")

To prove reproducibility, run the evaluation script against the 50 synthetic scenarios defined in `tests/golden_dataset.json`.

```bash
python tests/evaluate_system.py

```


