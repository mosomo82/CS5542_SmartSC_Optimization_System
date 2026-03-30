# 📖 Detailed Documentation

HyperLogistics is a Smart Supply Chain Optimization System combining Spatial SQL, Multi-Agent Logic, and RAG.

### 1. Layer 1: Data Lake (Snowflake)
- **Ingestion:** Snowpipe and local Python scripts populate the Bronze layer from S3.
- **Preprocessing:** SQL transformations and Python UDFs turn raw telematics into Silver analytics-ready tables.

### 2. Layer 2: Intelligence (Cortex & ReMindRAG)
- **Agent Reasoning:** A LangChain ReAct loop runs on **Snowflake Cortex Llama 3 70B**.
- **Contextual Retrieval:** `ReMindRAG` traverses the logistics knowledge graph to find historical precedents and regulatory constraints.

### 3. Layer 3: Risk Forecasting (SRSNet)
- **Temporal Patching:** SRSNet (NeurIPS 2025) forecasts risk propagation across middle-mile patches (4–8h windows).
- **Consensus Planning:** A multi-agent negotiation gates all final routing decisions to ensure they are safe, efficient, and compliant.

### 4. Repository Structure
- `src/agents/`: Autonomous decision logic.
- `src/ingestion/`: Cloud and local data movement.
- `src/sql/`: Database schemas and Medallion transformations.
- `src/app/`: Streamlit interactive dashboard.
- `tests/`: Evaluation and unit testing suite.
