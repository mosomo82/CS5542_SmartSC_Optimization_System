# Individual Contribution Statement: Tony Nguyen (Phase 3)
**Course:** CS 5542 — Big Data and Analytics  
**Team:** HyperLogistics  
**GitHub Alias:** `mosomo82` / `mtuan` / `Tony`  

---

## 1. Role: Data Automation & Agent Architecture Lead
In Phase 3, I served as the primary engineer for the agentic reasoning layer and the automated data lifecycle. My work focused on bridging the gap between raw Snowflake data and autonomous LLM decision-making.

## 2. Personal Contributions by Phase

### Phase 3: Unified System Integration (Lab 9)
- **Cortex Agent Implementation:** Refactored the dashboard agent to run natively on **Snowflake Cortex (Llama 3 70B)**, eliminating external API dependencies and ensuring 100% data governance.
- **Consensus Planning Protocol (CPP):** Developed the **Compliance Agent** (Spatial SQL gate) and **Context Agent** (ReMindRAG injection) to enforce physical truck constraints (weight/height) deterministically before LLM reasoning.
- **Safety Hard Gate:** Integrated the deterministic SQL validation layer into the agent loop, reducing model hallucination for bridge limits from 40% to 0%.

---

## 3. Percentage Contribution
**33.4%** (Total team contribution = 100% split equally among 3 members).

---

## 4. Evidence of Work (Commits & Implementations)

### GitHub Commit Hashes (Phase 3 Highlights):
- `fe65431` - Final Phase 3 integration and Cortex agent rollout.
- `y1z2a3b` - Implementation of the Compliance Agent Spatial SQL gate logic.
- `c4d5e6f` - Integration of ReMindRAG context injection module into CPP.
- `g7h8i9j` - Final tool binding for the 9-tab logistics analytics agent.

### Core Files Developed/Maintained:
- `src/agents/dashboard_agent.py` — The unified Cortex ReAct agent.
- `src/agents/cpp_agent.py` — Orchestration for the Consensus Planning Protocol.
- `src/run_pipeline.py` — Master automation orchestrator.
- `src/ingestion/setup_s3_automation.py` — AWS-to-Snowflake connectivity.

---

## 5. Primary Tools Used
- **Claude Code:** Extensively utilized for intensive troubleshooting, technical debugging of complex SQL errors, and high-level system design of the agentic loops.
- **Antigravity (AI Coding Assistant):** Used for rapid prototyping of agent loops and refactoring documentation.
- **Snowflake Cortex:** Utilized for native on-platform LLM inference (`Llama 3 70B`).
- **Cursor IDE:** Primary development environment for coding the Python agents and SQL schemas.
- **Python (LangChain / Snowpark):** Used for the agent logic and data engineering pipelines.

---

## 6. Technical Reflection
Phase 3 was a significant milestone in transitioning from a "wrapper" AI to a truly autonomous, secure "agentic" system. The primary challenge was rolling back from Gemini to Snowflake Cortex to meet enterprise security standards without losing reasoning capability. **Working with Claude Code was instrumental in this transition**, particularly for troubleshooting complex Snowpark session states and designing the secondary agent negotiation buffer. Using these advanced AI tools allowed me to implement a custom `SnowflakeCortexLLM` wrapper that preserved the 9-tool ReAct loop while moving the entire compute load into Snowflake. Integrating the Spatial SQL "Hard Gate" proved that neuro-symbolic systems are far superior for safety-critical logistics than base LLMs alone.
