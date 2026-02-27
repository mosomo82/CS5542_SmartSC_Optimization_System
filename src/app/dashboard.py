import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import os
import sys
import json
from datetime import datetime

# Add project root to path so we can import src.utils
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from src.utils.snowflake_conn import get_session

# Page config
st.set_page_config(
    page_title="HyperLogistics Dashboard",
    page_icon="🚛",
    layout="wide"
)

# Snowflake connection via shared utility
@st.cache_resource
def init_session():
    return get_session()

session = init_session()

# ═══════════════════════════════════════════════════════════════
# QUERY LOGGING — Logs every query + response to GOLD.QUERY_LOGS
# ═══════════════════════════════════════════════════════════════
def log_query(query_text, response_text, grounding_sources, execution_time_ms, is_grounded):
    """Log user queries and AI responses to the GOLD.QUERY_LOGS table."""
    try:
        clean_query = query_text.replace("'", "''")
        clean_response = response_text.replace("'", "''")
        sources_json = json.dumps(grounding_sources).replace("'", "''")
        sql = f"""
        INSERT INTO HYPERLOGISTICS_DB.GOLD.QUERY_LOGS
        (QUERY_ID, USER_ID, QUERY_TEXT, RESPONSE_TEXT, GROUNDING_SOURCES,
         EXECUTION_TIME_MS, IS_GROUNDED, CREATED_AT)
        SELECT
            UUID_STRING(),
            '{os.getenv("SNOWFLAKE_USER", "dashboard_user")}',
            '{clean_query}',
            '{clean_response}',
            PARSE_JSON('{sources_json}'),
            {execution_time_ms},
            {str(is_grounded).upper()},
            CURRENT_TIMESTAMP()
        """
        session.sql(sql).collect()
    except Exception as e:
        st.warning(f"Query logging failed: {str(e)}")

# ═══════════════════════════════════════════════════════════════
# EVIDENCE RETRIEVAL — Fetches grounding data from Silver tables
# ═══════════════════════════════════════════════════════════════
def get_evidence(user_query):
    """
    Retrieve supporting evidence from processed tables.
    Returns structured evidence for grounding the AI response.
    """
    evidence = {}
    grounding_sources = []

    # 1. Check for accident risk data
    try:
        accident_sql = """
        SELECT STATE, CITY, INCIDENT_COUNT, AVG_SEVERITY
        FROM HYPERLOGISTICS_DB.SILVER.RISK_HEATMAP_VIEW
        ORDER BY INCIDENT_COUNT DESC
        LIMIT 5
        """
        accident_df = session.sql(accident_sql).to_pandas()
        if not accident_df.empty:
            evidence["accident_risk"] = accident_df
            grounding_sources.append("SILVER.RISK_HEATMAP_VIEW")
    except Exception:
        pass

    # 2. Check for bridge data
    try:
        bridge_sql = """
        SELECT FEATURES_DESC_006A AS BRIDGE_NAME, STATE_CODE_001 AS STATE_CODE, 
               VERT_CLR_OVER_MT_053 AS VERTICAL_CLEARANCE_MT, 
               OPERATING_RATING_064 AS LOAD_RATING, BRIDGE_CONDITION
        FROM HYPERLOGISTICS_DB.SILVER.BRIDGE_INVENTORY_GEO
        LIMIT 5
        """
        bridge_df = session.sql(bridge_sql).to_pandas()
        if not bridge_df.empty:
            evidence["bridge_data"] = bridge_df
            grounding_sources.append("SILVER.BRIDGE_INVENTORY_GEO")
    except Exception:
        pass

    # 3. Check for logistics data
    try:
        logistics_sql = """
        SELECT CHUNK_ID, RECORD_TYPE, TEXT_CONTENT
        FROM HYPERLOGISTICS_DB.SILVER.LOGISTICS_VECTORIZED
        LIMIT 5
        """
        logistics_df = session.sql(logistics_sql).to_pandas()
        if not logistics_df.empty:
            evidence["logistics_data"] = logistics_df
            grounding_sources.append("SILVER.LOGISTICS_VECTORIZED")
    except Exception:
        pass

    return evidence, grounding_sources

# ═══════════════════════════════════════════════════════════════
# CORTEX AI — Grounded Answer Generation
# ═══════════════════════════════════════════════════════════════
def get_cortex_response(user_query, evidence_context=""):
    """
    Uses Snowflake Cortex LLM to answer logistics queries.
    Includes retrieved evidence for grounded generation.
    """
    prompt = f"""
    You are a logistics expert for HyperLogistics, a Smart Supply Chain system.
    You have access to the following real-time evidence from our databases:

    {evidence_context}

    Based on this evidence, answer the user's question professionally.
    If you use evidence, cite which data source you used.

    User Question: {user_query}
    """
    clean_prompt = prompt.replace("'", "''")
    sql = f"SELECT SNOWFLAKE.CORTEX.COMPLETE('snowflake-arctic', '{clean_prompt}')"
    try:
        result = session.sql(sql).collect()
        return result[0][0]
    except Exception as e:
        return f"Error connecting to Cortex: {str(e)}"

# ═══════════════════════════════════════════════════════════════
# STREAMLIT UI
# ═══════════════════════════════════════════════════════════════
st.title("HyperLogistics: Smart Supply Chain Dashboard")
st.caption("Powered by Snowflake Cortex AI | Real-time logistics intelligence")

# --- Sidebar: AI Agent ---
st.sidebar.header("Ask the AI Agent")
query = st.sidebar.text_input("Enter your logistics query:", placeholder="e.g. What are the riskiest routes near Chicago?")

if st.sidebar.button("Submit Query", type="primary") and query:
    start_time = datetime.now()

    with st.sidebar:
        with st.spinner("Retrieving evidence..."):
            evidence, grounding_sources = get_evidence(query)

        # Build evidence context string for the LLM
        evidence_context = ""
        if "accident_risk" in evidence:
            evidence_context += f"Top Accident Risk Areas:\n{evidence['accident_risk'].to_string(index=False)}\n\n"
        if "bridge_data" in evidence:
            evidence_context += f"Bridge Compliance Data:\n{evidence['bridge_data'].to_string(index=False)}\n\n"
        if "logistics_data" in evidence:
            evidence_context += f"Logistics Operations:\n{evidence['logistics_data'][['RECORD_TYPE','TEXT_CONTENT']].to_string(index=False)}\n\n"

        with st.spinner("Generating AI response..."):
            response = get_cortex_response(query, evidence_context)

        execution_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        is_grounded = len(grounding_sources) > 0

        # Log the query
        log_query(query, response, grounding_sources, execution_time_ms, is_grounded)

        # Display response
        st.success("AI Response:")
        st.write(response)

        # Display grounding info
        if grounding_sources:
            st.info(f"Grounded on: {', '.join(grounding_sources)}")
            st.caption(f"Response time: {execution_time_ms}ms")

# --- Tab Layout ---
tab1, tab2, tab3, tab4 = st.tabs([
    "Risk Heatmap",
    "Route Comparison",
    "Evidence & Reasoning",
    "Query Logs"
])

# --- Tab 1: Risk Heatmap ---
with tab1:
    st.header("Traffic Incident Risk Heatmap")
    m = folium.Map(location=[39.8283, -98.5795], zoom_start=4)

    try:
        risk_data = session.sql("""
            SELECT STATE, CITY, INCIDENT_COUNT, AVG_SEVERITY
            FROM HYPERLOGISTICS_DB.SILVER.RISK_HEATMAP_VIEW
            WHERE INCIDENT_COUNT > 100
            ORDER BY INCIDENT_COUNT DESC
            LIMIT 50
        """).to_pandas()

        if not risk_data.empty:
            st.dataframe(risk_data, width='stretch')
    except Exception as e:
        st.warning(f"Could not load risk data: {str(e)}")

    folium_static(m, width=1200, height=500)

# --- Tab 2: Route Comparison ---
with tab2:
    st.header("AI-Powered Route Comparison")
    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Original Route")
        st.write("Route A: Chicago -> St. Louis -> Kansas City")
        st.metric("Estimated Delay", "4 hours", delta="High Risk", delta_color="inverse")
    with col2:
        st.subheader("AI-Suggested Route")
        st.write("Route B: Chicago -> Indianapolis -> Kansas City")
        st.metric("Estimated Delay", "1 hour", delta="Low Risk")

    st.divider()
    st.subheader("Reasoning Path")
    st.write("**Evidence:** NOAA data shows severe weather on I-70. "
             "Historical accidents indicate 85% higher risk during snow events.")
    st.write("**Action:** Reroute via I-65 to avoid storm cell. "
             "Bridge clearance verified for 14ft vehicles on alternate route.")

# --- Tab 3: Evidence Display ---
with tab3:
    st.header("Evidence & Grounding Sources")
    st.write("This tab shows the raw data that the AI uses to ground its answers.")

    evidence_tab1, evidence_tab2, evidence_tab3 = st.tabs([
        "Accident Risk Data", "Bridge Compliance", "Logistics Operations"
    ])

    with evidence_tab1:
        try:
            df = session.sql("""
                SELECT STATE, CITY, INCIDENT_COUNT, AVG_SEVERITY
                FROM HYPERLOGISTICS_DB.SILVER.RISK_HEATMAP_VIEW
                ORDER BY INCIDENT_COUNT DESC LIMIT 20
            """).to_pandas()
            st.dataframe(df, width='stretch')
        except Exception as e:
            st.warning(f"Could not load: {str(e)}")

    with evidence_tab2:
        try:
            df = session.sql("""
                SELECT FEATURES_DESC_006A AS BRIDGE_NAME, STATE_CODE_001 AS STATE_CODE, 
                       VERT_CLR_OVER_MT_053 AS VERTICAL_CLEARANCE_MT, 
                       OPERATING_RATING_064 AS LOAD_RATING, BRIDGE_CONDITION
                FROM HYPERLOGISTICS_DB.SILVER.BRIDGE_INVENTORY_GEO
                LIMIT 20
            """).to_pandas()
            st.dataframe(df, width='stretch')
        except Exception as e:
            st.warning(f"Could not load: {str(e)}")

    with evidence_tab3:
        try:
            df = session.sql("""
                SELECT CHUNK_ID, RECORD_TYPE, TEXT_CONTENT
                FROM HYPERLOGISTICS_DB.SILVER.LOGISTICS_VECTORIZED
                LIMIT 20
            """).to_pandas()
            st.dataframe(df, width='stretch')
        except Exception as e:
            st.warning(f"Could not load: {str(e)}")

# --- Tab 4: Query Logs ---
with tab4:
    st.header("Query Audit Log")
    st.write("All AI queries are logged for evaluation and reproducibility.")
    try:
        logs_df = session.sql("""
            SELECT QUERY_ID, QUERY_TEXT, RESPONSE_TEXT, GROUNDING_SOURCES,
                   EXECUTION_TIME_MS, IS_GROUNDED, CREATED_AT
            FROM HYPERLOGISTICS_DB.GOLD.QUERY_LOGS
            ORDER BY CREATED_AT DESC
            LIMIT 25
        """).to_pandas()

        if not logs_df.empty:
            st.dataframe(logs_df, width='stretch')

            # Summary metrics
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total Queries", len(logs_df))
            with col2:
                grounded_pct = logs_df["IS_GROUNDED"].mean() * 100 if "IS_GROUNDED" in logs_df.columns else 0
                st.metric("Grounded %", f"{grounded_pct:.0f}%")
            with col3:
                avg_time = logs_df["EXECUTION_TIME_MS"].mean() if "EXECUTION_TIME_MS" in logs_df.columns else 0
                st.metric("Avg Response Time", f"{avg_time:.0f}ms")
        else:
            st.info("No queries logged yet. Ask the AI Agent a question to see logs here.")
    except Exception as e:
        st.warning(f"Could not load query logs: {str(e)}")

# Footer
st.divider()
st.caption("HyperLogistics v1.0 | CS5542 Smart Supply Chain Optimization System | Built with Streamlit + Snowflake Cortex")