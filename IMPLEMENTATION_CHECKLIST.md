# HyperLogistics Implementation Checklist

Follow this checklist to set up HyperLogistics correctly from start to finish.

## ✅ Phase 1: Environment Setup (30 minutes)

- [ ] **Clone Repository**
  ```bash
  git clone https://github.com/mosomo82/CS5542_SmartSC_Optimization_System.git
  cd CS5542_SmartSC_Optimization_System
  ```

- [ ] **Create Python Virtual Environment**
  ```bash
  python -m venv venv
  .\venv\Scripts\activate  # Windows
  # or
  source venv/bin/activate  # Linux/Mac
  pip install -r requirements.txt
  ```

- [ ] **Copy Environment Template**
  ```bash
  cp .env.template .env
  # OR on Windows:
  copy .env.template .env
  ```

- [ ] **Fill in .env File**
  ```
  SNOWFLAKE_ACCOUNT=<your_account_id>
  SNOWFLAKE_USER=<your_username>
  SNOWFLAKE_PASSWORD=<your_password>
  SNOWFLAKE_WAREHOUSE=COMPUTE_WH
  SNOWFLAKE_DATABASE=HYPERLOGISTICS_DB
  
  AWS_REGION=us-east-1
  S3_BUCKET=<your-bucket-name>
  SNOWFLAKE_ROLE_ARN=<your-role-arn>
  ```

## ✅ Phase 2: AWS Setup (45 minutes)

- [ ] **Validate AWS Credentials**
  ```bash
  aws sts get-caller-identity
  # Should show your account ID and user
  ```

- [ ] **Get AWS Account ID**
  ```bash
  aws sts get-caller-identity --query Account --output text
  # Save this ID - you'll need it
  ```

- [ ] **Create/Validate IAM Role**
  ```bash
  python src/ingestion/validate_aws_role.bat  # Windows
  # or
  ./src/ingestion/validate_aws_role.sh        # Linux/Mac
  ```

- [ ] **Create S3 Bucket Structure**
  ```bash
  .\src\ingestion\create_s3_bucket.bat  # Windows
  # or
  bash src/ingestion/create_s3_bucket.sh  # Linux/Mac
  ```

- [ ] **Generate Bucket Policy & Apply**
  ```bash
  python src/ingestion/setup_s3_automation.py
  aws s3api put-bucket-policy --bucket YOUR_BUCKET --policy file://s3_bucket_policy.json
  ```

- [ ] **Update .env with AWS Details**
  ```
  SNOWFLAKE_ROLE_ARN=arn:aws:iam::YOUR_ACCOUNT_ID:role/SnowflakeS3Role
  S3_BUCKET=your-actual-bucket-name
  ```

## ✅ Phase 3: Snowflake Setup (20 minutes)

**IMPORTANT: Run SQL scripts in order!**

- [ ] **Step 1: Create Database**
  - Open Snowflake Worksheets
  - Copy entire contents of: `src/sql/00_create_database.sql`
  - Paste into worksheet and run
  - Verify: `SHOW DATABASES LIKE 'HYPERLOGISTICS%';`

- [ ] **Step 2: Setup NOAA External Table (Optional)**
  - Copy entire contents of: `src/sql/01_setup_noaa.sql`
  - Paste into worksheet and run
  - Verify: `SHOW TABLES IN HYPERLOGISTICS_DB.BRONZE;`

- [ ] **Step 3: Setup S3 Automation**
  - Open: `src/sql/02_setup_s3_automation.sql`
  - Replace placeholders:
    - `your-hyperlogistics-bucket` → your actual bucket
    - `YOUR_ACCOUNT_ID` → your AWS account ID
    - `SnowflakeS3Role` → your role name
  - Copy updated contents into worksheet and run
  - Verify: `SHOW PIPES IN HYPERLOGISTICS_DB.BRONZE;`

## ✅ Phase 4: Data Loading (30 minutes)

- [ ] **Download Datasets**
  - [ ] DataCo: https://www.kaggle.com/datasets/shashwatwork/dataco-smart-supply-chain-for-big-data-analysis
  - [ ] US Accidents: https://www.kaggle.com/datasets/sobhanmoosavi/us-accidents
  - [ ] Bridges: https://geodata.bts.gov/datasets/national-bridge-inventory/
  - Place in `data/` folder

- [ ] **Upload to S3**
  ```bash
  python upload_to_s3.py
  # This uploads data to S3 and Snowpipe auto-ingests it
  ```

- [ ] **Verify Data Ingestion**
  ```sql
  SELECT COUNT(*) FROM HYPERLOGISTICS_DB.BRONZE.RAW_LOGISTICS;
  SELECT COUNT(*) FROM HYPERLOGISTICS_DB.BRONZE.TRAFFIC_INCIDENTS;
  select task count(*) FROM HYPERLOGISTICS_DB.BRONZE.BRIDGE_INVENTORY;
  ```

## ✅ Phase 5: Preprocessing (15 minutes)

- [ ] **Run Preprocessing Scripts**
  ```bash
  python src/preprocessing/preprocess_dataco.py
  python src/preprocessing/preprocess_accidents.py
  python src/preprocessing/preprocess_weather.py
  python src/preprocessing/preprocess_bridges.py
  ```

- [ ] **Verify Silver Tables**
  ```sql
  SELECT COUNT(*) FROM HYPERLOGISTICS_DB.SILVER.CLEANED_LOGISTICS;
  SELECT COUNT(*) FROM HYPERLOGISTICS_DB.SILVER.RISK_HEATMAP;
  ```

## ✅ Phase 6: Training & Deployment (1 hour)

- [ ] **Train SRSNet Model**
  ```bash
  jupyter lab notebooks/srsnet_training.ipynb
  # Follow the notebook cells
  ```

- [ ] **Deploy Streamlit App**
  ```bash
  streamlit run src/app/dashboard.py
  # Opens in browser at http://localhost:8501
  ```

## ✅ Phase 7: Evaluation (15 minutes)

- [ ] **Run Evaluation Tests**
  ```bash
  python tests/evaluate_system.py
  # Tests against golden dataset
  ```

- [ ] **Check Query Logs**
  ```sql
  SELECT * FROM HYPERLOGISTICS_DB.GOLD.QUERY_LOGS ORDER BY CREATED_AT DESC LIMIT 10;
  ```

## 🔧 Troubleshooting

| Error | Solution |
|-------|----------|
| `HYPERLOGISTICS_DB does not exist` | Run `src/sql/00_create_database.sql` first |
| `Invalid principal in policy` | See `docs/troubleshoot_invalid_principal.md` |
| `Access Denied` on S3 | Verify bucket policy & IAM role |
| `Table not found` in pipes | Create tables with `00_create_database.sql` |
| Python packages missing | Run `pip install -r requirements.txt` |

## 📊 Expected Results

After completing all phases:
- ✅ Database HYPERLOGISTICS_DB exists
- ✅ 3 Medallion layers (Bronze, Silver, Gold)
- ✅ Data loaded from S3 via Snowpipe
- ✅ Preprocessing completed
- ✅ Streamlit dashboard running
- ✅ Evaluation tests passed

## 📚 Documentation References

- **S3 Setup**: `docs/s3_automation_guide.md`, `docs/s3_quick_reference.md`
- **Snowflake Setup**: `docs/snowflake_setup.md`, `docs/fix_db_not_exist.md`
- **Troubleshooting**: `docs/troubleshoot_invalid_principal.md`
- **Full Details**: `docs/detailed_documentation.md`
- **Reproducibility**: `reproducibility/README_repoductibility.md`

## ✨ Success Criteria

You're done when:
1. All SQL scripts run without errors
2. Data is loaded into all Bronze tables
3. Preprocessing scripts complete successfully
4. Streamlit app starts and loads data
5. Evaluation tests all pass