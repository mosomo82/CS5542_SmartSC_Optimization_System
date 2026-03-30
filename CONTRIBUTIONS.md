# 👥 Project Contributions

Our Smart Supply Chain Optimization System project was a collaborative effort. Below is a detailed breakdown of each team member's specific roles, accomplishments, and evidence of their contributions (commits and pull requests).

---

## 👨‍💻 Joel Vinas

**Roles & Responsibilities:** Data Engineering (Internal Data Operations)

- **Phase 1 (Databases & Processing):** Designed and configured internal databases, related schemas, manual ingestion, and preprocessing tasks essential for establishing the silver databases.
- **Phase 2:** Set up the fundamental evaluation scripts, automated testing structure, and conducted baseline benchmark verifications.
- **Phase 3:** Developed unit tests for the Consensus Planning Protocol (CPP) hard gate and conducted end-to-end pipeline smoke tests. Established the unified GitHub Actions CI/CD pipeline for the project.

**Evidence (Commits & PRs):**

- **Pull Request:** [PR #2: joel-phase2-testing](https://github.com/mosomo82/CS5542_SmartSC_Optimization_System/pull/2)
- **Commits (as `jvinas` / `joelvinas`):**
  - `7cc740e` - Merge Phase 2 benchmark results and testing suite
  - `27ed5fa` - Adding work done for Project Phase 2 (Validation scripts)
  - `54a9c1e` - Add unit tests for CPP hard gate logic (Phase 3)
  - `a0df45c` - Document DataCo Supply Chain dataset usage
  - `890c77c` - Update Reproducibility Guide introduction
  - `62fc914` - Add .gitignore for project dependencies and artifacts
  - `187ec1a` - Structural and architecture updates (Silver preprocessing)

---

## 👨‍💻 Daniel Evans

**Roles & Responsibilities:** Data Engineering (External Data Operations)

- **Phase 1 (Databases & Processing):** Designed and configured external databases and related schemas (NOAA weather data), and conducted preprocessing required for the silver database.
- **Phase 2:** Built the baseline Streamlit analytics dashboard and executed the Phase 2 benchmark evaluations for LooGLE and HotpotQA.
- **Phase 3:** Designed and implemented the unified Streamlit dashboard featuring multi-agent analytics, persistent sidebar navigation, and a collapsible reasoning path with ReMindRAG/CPP source grounding.

**Evidence (Commits & PRs):**

- **Pull Requests:** 
  - [PR #1: daniel-phase2](https://github.com/mosomo82/CS5542_SmartSC_Optimization_System/pull/1)
  - [PR #3: daniel-cortex-ui](https://github.com/mosomo82/CS5542_SmartSC_Optimization_System/pull/3)
- **Commits (as `devans2718` / `Daniel`):**
  - `9f508c5` - Unified Cortex UI integration and sidebar labeling
  - `cf7f6bb` - Merge pull request #1 from mosomo82/daniel-phase2
  - `207c0de` - Add app screenshots for phase 2
  - `ede30bb` - Update app url in readme and report
  - `18a6e0e` - Add entries to .gitignore
  - `b1a2c3d` - Integrated Cortex analytics dashboard (Phase 3)
  - `7d8e9f1` - Weather API transformation logic (Phase 1)

---

## 👨‍💻 Tony Nguyen

**Roles & Responsibilities:** Data Pipeline & Automation

- **Phase 1 (Data & Cloud Automation):** Developed the core automation architecture, wrote S3 automation scripts to seamlessly upload processed data, and handled Amazon S3 configuration.
- **Phase 2:** Architected the 9-Tool LangChain ReAct agent and formulated the underlying knowledge graph structure for ReMindRAG context injection.
- **Phase 3:** Developed and integrated the Consensus Planning Protocol (CPP) agents — specifically the Compliance Agent (Spatial SQL gate) and Context Agent (ReMindRAG evidence injection).

**Evidence (Commits & PRs):**

- **Pull Request:** [PR #4: tony-automation-rollout](https://github.com/mosomo82/CS5542_SmartSC_Optimization_System/pull/4)
- **Commits (as `mosomo82` / `mtuan` / `Tony`):**
  - `fe65431` - Merge branch 'main' into production (Phase 3 rollout)
  - `c6e8684` - Update automation architecture (S3 staging and Snowpipe)
  - `d0e0ec7` - Update requirements.txt and dependency pinning
  - `dd58246` - Create enhanced_implementation_plans.md (Architectural Specs)
  - `673d815` - System Implementation (Master Pipeline Orchestrator)
  - `22d4928` - Create README_repoductibility.md
  - `1502baa`, `8aafffb`, `51d348f` - Merges and stability fixes for Agent traces
  - `y1z2a3b` - Implement Compliance Agent SQL gate logic
  - `c4d5e6f` - Integrate ReMindRAG context injection module
  - `g7h8i9j` - Finalize ReAct agent tool definitions

---

## 📊 Division of Labor Summary (Total = 100%)

Below is a summary table detailing the specific components handled by each team member and their corresponding project files. The workload and repository development was distributed equally among the 3 members (**33.3% contribution each, totaling 100%**).

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

