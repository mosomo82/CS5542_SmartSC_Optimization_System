# 👥 Project Contributions

Our Smart Supply Chain Optimization System project was a collaborative effort. Below is a detailed breakdown of each team member's specific roles, accomplishments, and evidence of their contributions (commits and pull requests).

---

## 👨‍💻 Joel Vinas
**Roles & Responsibilities:** Data Engineering (Internal Data Operations)
* **Databases:** Designed and configured internal databases and related schemas.
* **Data Processing:** Conducted manual ingestion and performed preprocessing tasks essential for establishing the silver databases.

**Evidence (Commits & PRs):**
* **Commits (as `jvinas` / `joelvinas`):**
  * `a0df45c` - Document DataCo Supply Chain dataset usage
  * `890c77c` - Update Reproducibility Guide introduction
  * `62fc914` - Add .gitignore for project dependencies and artifacts
  * `187ec1a` - Structural and architecture updates

---

## 👨‍💻 Daniel Evans
**Roles & Responsibilities:** Data Engineering (External Data Operations)
* **Databases:** Designed and configured external databases and related schemas (NOAA weather data).
* **Data Processing:** Conducted preprocessing required for the silver database.

**Evidence (Commits & PRs):**
* **Pull Request:** [PR #1: daniel-phase2](https://github.com/mosomo82/CS5542_SmartSC_Optimization_System/pull/1)
* **Commits (as `devans2718` / `Daniel`):**
  * `cf7f6bb` - Merge pull request #1 from mosomo82/daniel-phase2
  * `207c0de` - Add app screenshots for phase 2
  * `ede30bb` - Update app url in readme and report
  * `18a6e0e` - Add entries to .gitignore

---

## 👨‍💻 Tony Nguyen
**Roles & Responsibilities:** Data Pipeline & Automation
* **Data Automation:** Developed the core automation architecture for the project.
* **Scripting:** Wrote automation scripts dedicated to seamlessly uploading processed data.
* **Cloud Integration:** Handled the setup and configuration of Amazon S3 automation.

**Evidence (Commits & PRs):**
* **Commits (as `mosomo82` / `mtuan`):**
  * `d0e0ec7` - Update requirements.txt
  * `dd58246` - Create enhanced_implementation_plans.md
  * `673d815` - System Implementation
  * `22d4928` - Create README_repoductibility.md
  * `1502baa`, `8aafffb`, `51d348f` - Maintained branch stability and merges

---

## 📊 Division of Labor Summary

Below is a summary table detailing the specific components handled by each team member and their corresponding project files.

| Team Member     | Role / Component Area | Key Responsibilities | Primary Files / Artifacts |
|-----------------|-----------------------|----------------------|---------------------------|
| **Joel Vinas**  | **Internal Data Engineering** | Set up internal Snowflake databases (`SMART_SUPPLY_CHAIN_DB`). Manual data ingestion loops and standard silver-level preprocessing for operational data. | `src/sql/00_create_database.sql`<br>`src/ingestion/ingest_*.py`<br>`src/preprocessing/preprocess_dataco.py`<br>`src/preprocessing/preprocess_logistics.py`<br>`src/preprocessing/preprocess_accidents.py`<br>`src/preprocessing/preprocess_bridges.py` |
| **Daniel Evans**| **External Data Engineering & App** | Configured external NOAA weather database and integrated weather logic. Processed external variables to silver layer. Delivered and synced the final Streamlit App UI. | `src/sql/01_setup_noaa.sql`<br>`src/preprocessing/preprocess_weather.py`<br>`src/app/dashboard.py`<br>`README.md` (App Deployment Links) |
| **Tony Nguyen** | **Data Automation & Architecture** | Created the overarching data automation pipeline. Set up Snowflake/S3 connection scripts, continuous file processing loops, system verification protocols, and reproducibility guides. | `src/ingestion/setup_s3_automation.py`<br>`src/sql/02_setup_s3_automation.sql`<br>`src/run_pipeline.py`<br>`src/verify_pipeline.py`<br>`src/utils/snowflake_conn.py`<br>`README_repoductibility.md` |

---

## 🏗️ Team Components

| Component | Files |
|-----------|-------|
| Snowflake environment setup (databases, schemas, tables) | `src/sql/00_create_database.sql` |
| NOAA external dataset setup & schemas | `src/sql/01_setup_noaa.sql` |
| AWS S3 external stage + COPY INTO from S3 setup | `src/sql/02_setup_s3_automation.sql`, `src/ingestion/setup_s3_automation.py` |
| Internal staging + manual ingestion scripts | `src/ingestion/ingest_*.py` |
| Derived views / Streamlit Dashboard | `src/app/dashboard.py` |
| Data preprocessing and analytical transformations | `src/preprocessing/preprocess_*.py` |
| Automated master orchestrator pipeline (local + S3 modes) | `src/run_pipeline.py` |
| System/Pipeline verification protocol | `src/verify_pipeline.py` |
| Snowflake connectivity utilities | `src/utils/snowflake_conn.py` |
s