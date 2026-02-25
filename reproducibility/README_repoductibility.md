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

## ☁️ Step 1.5: AWS S3 Setup (For Automated Loading)

If you have an S3 bucket and want **fully automated data loading**, follow these steps:

### 1.5.1 Configure AWS IAM Role for Snowflake

1. **Create IAM Role:**
   - Go to AWS IAM Console
   - Create new role with "Another AWS account" as trusted entity
   - Enter your Snowflake account ID (from your Snowflake account URL)
   - Attach `AmazonS3ReadOnlyAccess` policy

2. **Get Role ARN:**
   - Copy the ARN: `arn:aws:iam::your-account-id:role/your-snowflake-role-arn`

### 1.5.2 Configure S3 Bucket

1. **Create Bucket Structure:**
   ```
   your-s3-bucket/
   ├── logistics/     # For DataCo dataset
   ├── accidents/     # For US Accidents
   └── bridges/       # For Bridge Inventory
   ```

2. **Apply Bucket Policy:**
   ```bash
   python src/ingestion/setup_s3_automation.py
   ```
   This generates `s3_bucket_policy.json` - apply it to your S3 bucket.

### 1.5.3 Setup Snowflake Integration

1. **Run SQL Setup:**
   ```sql
   -- Execute src/sql/02_setup_s3_automation.sql in Snowflake
   -- Replace placeholders with your bucket name and role ARN
   ```

2. **Configure S3 Event Notifications (Optional for Full Automation):**
   - Create SQS queues for each dataset
   - Configure S3 to send events to SQS
   - Snowpipe will auto-poll the queues

### 1.5.4 Upload Data to S3

```bash
# Download datasets to local data/ folder first
python src/ingestion/setup_s3_automation.py  # Generates upload script
python upload_to_s3.py  # Uploads all datasets
```

**Benefits:** Once set up, new data files uploaded to S3 automatically trigger ingestion into Snowflake!

---

## ❄️ Step 1.6: Snowflake Database Setup

### 1.6.1 Create Database and Tables

Before ingesting data, set up your Snowflake database structure. Run these SQL scripts **in order** in Snowflake Worksheets:

1. **Create Database & Schemas:**
   ```sql
   -- Copy and paste entire contents of: src/sql/00_create_database.sql
   -- This creates HYPERLOGISTICS_DB, BRONZE, SILVER, GOLD schemas and all tables
   ```

2. **Optional - Setup NOAA External Table:**
   ```sql
   -- Copy and paste entire contents of: src/sql/01_setup_noaa.sql
   -- This connects to public NOAA S3 bucket for weather data
   ```

3. **Setup S3 Automation:**
   ```sql
   -- BEFORE RUNNING:
   -- 1. Open: src/sql/02_setup_s3_automation.sql
   -- 2. Replace:
   --    - your-hyperlogistics-bucket  →  Your actual S3 bucket
   --    - YOUR_ACCOUNT_ID             →  Your AWS Account ID (e.g., 123456789012)
   --    - SnowflakeS3Role             →  Your IAM role name
   -- 3. Then copy and paste into Snowflake Worksheet
   ```

**Troubleshooting:** If you get "HYPERLOGISTICS_DB does not exist", see [docs/fix_db_not_exist.md](../docs/fix_db_not_exist.md)

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


