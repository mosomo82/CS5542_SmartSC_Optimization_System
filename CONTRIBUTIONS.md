# 👥 Project Contributions

Our Smart Supply Chain Optimization System project was a collaborative effort. Below is a detailed breakdown of each team member's specific roles, accomplishments, and evidence of their contributions (commits and pull requests).

---

## 👨‍💻 Joel Vinas

**Roles & Responsibilities:** Data Engineering (Internal Data Operations)

- **Databases:** Designed and configured internal databases and related schemas.
- **Data Processing:** Conducted manual ingestion and performed preprocessing tasks essential for establishing the silver databases.
- **Lab 9 (Phase 2):** Developed unit tests for the Consensus Planning Protocol (CPP) hard gate and conducted end-to-end pipeline smoke tests. Established the unified GitHub Actions CI/CD pipeline for the project.

**Evidence (Commits & PRs):**

- **Commits (as `jvinas` / `joelvinas`):**
  - `a0df45c` - Document DataCo Supply Chain dataset usage
  - `890c77c` - Update Reproducibility Guide introduction
  - `62fc914` - Add .gitignore for project dependencies and artifacts
  - `187ec1a` - Structural and architecture updates

---

## 👨‍💻 Daniel Evans

**Roles & Responsibilities:** Data Engineering (External Data Operations)

- **Databases:** Designed and configured external databases and related schemas (NOAA weather data).
- **Data Processing:** Conducted preprocessing required for the silver database.
- **Lab 9 (Phase 2):** Designed and implemented the unified Streamlit dashboard featuring multi-agent analytics, persistent sidebar navigation, and a collapsible reasoning path with ReMindRAG/CPP source grounding. Executed Phase 2 benchmark evaluations for LooGLE/HotpotQA.

**Evidence (Commits & PRs):**

- **Pull Request:** [PR #1: daniel-phase2](https://github.com/mosomo82/CS5542_SmartSC_Optimization_System/pull/1)
- **Commits (as `devans2718` / `Daniel`):**
  - `cf7f6bb` - Merge pull request #1 from mosomo82/daniel-phase2
  - `207c0de` - Add app screenshots for phase 2
  - `ede30bb` - Update app url in readme and report
  - `18a6e0e` - Add entries to .gitignore

---

## 👨‍💻 Tony Nguyen

**Roles & Responsibilities:** Data Pipeline & Automation

- **Data Automation:** Developed the core automation architecture for the project.
- **Scripting:** Wrote automation scripts dedicated to seamlessly uploading processed data.
- **Cloud Integration:** Handled the setup and configuration of Amazon S3 automation.
- **Lab 9 (Phase 2):** Developed and integrated the Consensus Planning Protocol (CPP) agents — specifically the Compliance Agent (Spatial SQL gate) and Context Agent (ReMindRAG evidence injection).

**Evidence (Commits & PRs):**

- **Commits (as `mosomo82` / `mtuan`):**
  - `d0e0ec7` - Update requirements.txt
  - `dd58246` - Create enhanced_implementation_plans.md
  - `673d815` - System Implementation
  - `22d4928` - Create README_repoductibility.md
  - `1502baa`, `8aafffb`, `51d348f` - Maintained branch stability and merges

---

## 📊 Division of Labor Summary

Below is a summary table detailing the specific components handled by each team member and their corresponding project files.

| Team Member      | Role / Component Area                   | Key Responsibilities                                                                                                                                             | Primary Files / Artifacts                                                                                                    |
| ---------------- | --------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------- | ---------------------------------------------------------------------------------------------------------------------------- |
| **Joel Vinas**   | **Internal Data Engineering & Testing** | Internal Snowflake setup, manual ingestion loops, and silver preprocessing. **Lab 9:** Unified CI/CD pipeline and CPP unit testing.                              | `src/verify_pipeline.py`<br>`tests/test_cpp_gate.py`<br>`tests/test_pipeline.py`<br>`.github/workflows/ci.yml`               |
| **Daniel Evans** | **External Data Engineering & App**     | External NOAA configuration and weather logic integration. **Lab 9:** Unified Streamlit Dashboard (Analytics + CPP/RAG Reasoning Path) and Phase 2 benchmarking. | `src/app/dashboard.py`<br>`eval_results.json`<br>`ARCHITECTURE.md` (Design)<br>`README.md` (Lab 9 Changlog)                  |
| **Tony Nguyen**  | **Architecture & Multi-Agent Logic**    | S3/Snowflake automation architecture. **Lab 9:** CPP Consensus Planning Protocol agents, ReMindRAG-guided retrieval integration, and evidence injection logic.   | `src/agents/cpp_agent.py`<br>`src/agents/compliance_agent.py`<br>`src/agents/context_agent.py`<br>`ARCHITECTURE.md` (System) |

---

## 🏗️ Team Components

| Component                                                 | Files                                                                        |
| --------------------------------------------------------- | ---------------------------------------------------------------------------- |
| Snowflake environment setup (databases, schemas, tables)  | `src/sql/00_create_database.sql`                                             |
| NOAA external dataset setup & schemas                     | `src/sql/01_setup_noaa.sql`                                                  |
| AWS S3 external stage + COPY INTO from S3 setup           | `src/sql/02_setup_s3_automation.sql`, `src/ingestion/setup_s3_automation.py` |
| Internal staging + manual ingestion scripts               | `src/ingestion/ingest_*.py`                                                  |
| Derived views / Streamlit Dashboard                       | `src/app/dashboard.py`                                                       |
| Data preprocessing and analytical transformations         | `src/preprocessing/preprocess_*.py`                                          |
| Automated master orchestrator pipeline (local + S3 modes) | `src/run_pipeline.py`                                                        |
| System/Pipeline verification protocol                     | `src/verify_pipeline.py`                                                     |
| Snowflake connectivity utilities                          | `src/utils/snowflake_conn.py`                                                |

s
