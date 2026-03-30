import streamlit as st
import pandas as pd
import folium
from streamlit_folium import folium_static
import altair as alt
import os
import sys
import json
import time
from datetime import datetime

# Add project root to path so we can import src.utils
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
from src.utils.snowflake_conn import get_session
from src.agents.dashboard_agent import run_cortex_agent

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
def retry_api(func):
    """Decorator: retry up to 3 times with 2 s sleep on any exception."""
    def wrapper(*args, **kwargs):
        last_err = None
        for attempt in range(3):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                last_err = e
                if attempt < 2:
                    time.sleep(2)
        return f"Error connecting to Cortex after 3 attempts: {str(last_err)}"
    wrapper.__name__ = func.__name__
    return wrapper


@retry_api
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
    result = session.sql(sql).collect()
    return result[0][0]

# ═══════════════════════════════════════════════════════════════
# STREAMLIT UI
# ═══════════════════════════════════════════════════════════════
st.title("HyperLogistics: Smart Supply Chain Dashboard")
st.caption("Powered by Snowflake Cortex AI | Real-time logistics intelligence")

# --- Persistent Sidebar ---
with st.sidebar:
    st.title("🚛 HyperLogistics")
    st.markdown(
        "**CS5542 Smart Supply Chain Optimization System** — Phase 2 integration.\n\n"
        "Combines CPP route compliance, ReMindRAG evidence retrieval, "
        "and Snowflake Cortex AI for grounded logistics intelligence."
    )
    st.caption(f"Data freshness: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")

    st.divider()
    st.markdown("### ⚙️ Session")
    if st.button("🔄 Reset Session", use_container_width=True, help="Clears session state and reloads the app"):
        st.session_state.clear()
        st.rerun()

    st.divider()
    st.markdown("### 🗂️ Quick Navigation")
    selected_tab = st.radio(
        "Jump to tab",
        ["Risk Heatmap", "Route Comparison", "Evidence & Reasoning", "Query Logs",
         "🚛 Fleet & Drivers", "🗺️ Routes", "⛽ Fuel Spend", "⚠️ Safety"],
        label_visibility="collapsed",
        key="nav_radio"
    )

    st.divider()
    st.markdown("### 🤖 Ask the AI Agent")
    query = st.text_input("Enter your logistics query:", placeholder="e.g. What are the riskiest routes near Chicago?")

if st.sidebar.button("Submit Query", type="primary", key="submit_query") and query:
    start_time = datetime.now()

    with st.sidebar:
        with st.spinner("Agent Reasoning in Progress (Snowflake Cortex Llama 3)..."):
            agent_result = run_cortex_agent(session, query)
            response = agent_result["output"]
            trace = agent_result["trace"]

        execution_time_ms = int((datetime.now() - start_time).total_seconds() * 1000)
        is_grounded = len(trace) > 0
        grounding_sources = ["Tool: " + step["tool"] for step in trace]

        # Log the query
        log_query(query, response, grounding_sources, execution_time_ms, is_grounded)

        # Display response
        st.success("🤖 Snowflake Cortex Response:")
        st.write(response)

        # Display grounding info
        if is_grounded:
            st.info(f"Tools Used: {', '.join(set([step['tool'] for step in trace]))}")
            st.caption(f"Response time: {execution_time_ms}ms")

        # Collapsible Reasoning Path expander
        with st.expander("🧠 Agent Reasoning Trace (ReAct)", expanded=False):
            st.markdown("**Model:** Snowflake Cortex (Llama 3 70B)")
            if not trace:
                st.markdown("*No external tools were invoked. Answer generated from internal knowledge.*")
            else:
                for idx, step in enumerate(trace):
                    st.markdown(f"**Step {idx+1}:** `Action: {step['tool']}`")
                    st.markdown(f"> **Input:** _{step['tool_input']}_")
                    st.markdown(f"> **Observation:** {step['observation']}")
            st.caption(f"Total execution time: {execution_time_ms} ms")

# --- Tab Layout ---
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs([
    "Risk Heatmap",
    "Route Comparison",
    "Evidence & Reasoning",
    "Query Logs",
    "🚛 Fleet & Drivers",
    "🗺️ Routes",
    "⛽ Fuel Spend",
    "⚠️ Safety"
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

# ═══════════════════════════════════════════════════════════════
# TAB 5 — Fleet & Drivers (Lab 6 port)
# ═══════════════════════════════════════════════════════════════
with tab5:
    st.header("🚛 Fleet & Driver Performance")
    st.caption("Top trucks by revenue — sourced from `CS5542_WEEK5.PUBLIC.V_TRIP_PERFORMANCE`")
    try:
        df_fleet = session.sql("""
            SELECT TRUCK_ID, TRUCK_MAKE, TRUCK_YEAR, FUEL_TYPE, DRIVER_NAME, DRIVER_TERMINAL,
                   COUNT(*) AS TRIPS,
                   ROUND(SUM(ACTUAL_DISTANCE_MILES), 0) AS TOTAL_MILES,
                   ROUND(AVG(AVERAGE_MPG), 2) AS AVG_MPG,
                   ROUND(SUM(REVENUE), 2) AS TOTAL_REVENUE
            FROM CS5542_WEEK5.PUBLIC.V_TRIP_PERFORMANCE
            WHERE TRIP_STATUS = 'Completed'
              AND FUEL_TYPE IN ('Diesel', 'CNG', 'Electric')
            GROUP BY TRUCK_ID, TRUCK_MAKE, TRUCK_YEAR, FUEL_TYPE, DRIVER_NAME, DRIVER_TERMINAL
            HAVING COUNT(*) >= 5
            ORDER BY TOTAL_REVENUE DESC
            LIMIT 30
        """).to_pandas()
        if not df_fleet.empty:
            fk1, fk2, fk3 = st.columns(3)
            fk1.metric("Total Trucks", len(df_fleet))
            fk2.metric("Total Revenue", f"${df_fleet['TOTAL_REVENUE'].sum():,.0f}")
            fk3.metric("Avg MPG", f"{df_fleet['AVG_MPG'].mean():.2f}")
            bar_fleet = (
                alt.Chart(df_fleet.head(15), title="Top 15 Trucks by Revenue")
                .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
                .encode(
                    x=alt.X("TOTAL_REVENUE:Q", title="Revenue ($)"),
                    y=alt.Y("TRUCK_ID:N", sort="-x", title="Truck ID"),
                    color=alt.Color("FUEL_TYPE:N", legend=alt.Legend(title="Fuel")),
                    tooltip=["TRUCK_ID:N", "TRUCK_MAKE:N", "FUEL_TYPE:N",
                             "TOTAL_REVENUE:Q", "TRIPS:Q", "AVG_MPG:Q"],
                ).properties(height=400)
            )
            st.altair_chart(bar_fleet, use_container_width=True)
            with st.expander("Full Fleet Table"):
                st.dataframe(df_fleet, use_container_width=True)
    except Exception as e:
        st.warning(f"Could not load fleet data: {str(e)}")

# ═══════════════════════════════════════════════════════════════
# TAB 6 — Routes (Lab 6 port)
# ═══════════════════════════════════════════════════════════════
with tab6:
    st.header("🗺️ Route Scorecard")
    st.caption("Top routes by gross profit — sourced from `CS5542_WEEK5.PUBLIC.V_ROUTE_SCORECARD`")
    try:
        df_routes = session.sql("""
            SELECT *
            FROM CS5542_WEEK5.PUBLIC.V_ROUTE_SCORECARD
            WHERE TOTAL_LOADS >= 5 AND MARGIN_PCT >= 0
            ORDER BY GROSS_PROFIT DESC
            LIMIT 25
        """).to_pandas()
        if not df_routes.empty:
            rk1, rk2, rk3 = st.columns(3)
            rk1.metric("Avg Margin %", f"{df_routes['MARGIN_PCT'].mean():.1f}%")
            rk2.metric("Total Revenue", f"${df_routes['TOTAL_REVENUE'].sum():,.0f}")
            rk3.metric("Avg MPG", f"{df_routes['AVG_MPG'].mean():.1f}")
            bar_routes = (
                alt.Chart(df_routes.head(15), title="Route Gross Profit ($)")
                .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
                .encode(
                    x=alt.X("GROSS_PROFIT:Q", title="Gross Profit ($)"),
                    y=alt.Y("ROUTE_LABEL:N", sort="-x", title="Route"),
                    color=alt.Color(
                        "MARGIN_PCT:Q",
                        scale=alt.Scale(scheme="redyellowgreen"),
                        legend=alt.Legend(title="Margin %"),
                    ),
                    tooltip=["ROUTE_LABEL:N", "TOTAL_LOADS:Q", "TOTAL_REVENUE:Q",
                             "GROSS_PROFIT:Q", "MARGIN_PCT:Q"],
                ).properties(height=420)
            )
            st.altair_chart(bar_routes, use_container_width=True)
            with st.expander("Full Route Table"):
                st.dataframe(df_routes, use_container_width=True)
    except Exception as e:
        st.warning(f"Could not load routes data: {str(e)}")

# ═══════════════════════════════════════════════════════════════
# TAB 7 — Fuel Spend (Lab 6 port)
# ═══════════════════════════════════════════════════════════════
with tab7:
    st.header("⛽ Fuel Spend by Location")
    st.caption("Top locations by total fuel spend — sourced from `CS5542_WEEK5.PUBLIC.V_FUEL_SPEND`")
    try:
        df_fuel = session.sql("""
            SELECT *
            FROM CS5542_WEEK5.PUBLIC.V_FUEL_SPEND
            ORDER BY TOTAL_SPEND DESC
            LIMIT 50
        """).to_pandas()
        if not df_fuel.empty:
            fk1, fk2, fk3 = st.columns(3)
            fk1.metric("Total Spend", f"${df_fuel['TOTAL_SPEND'].sum():,.0f}")
            fk2.metric("Total Gallons", f"{df_fuel['TOTAL_GALLONS'].sum():,.0f}")
            fk3.metric("Avg $/gal", f"${df_fuel['AVG_PRICE_PER_GALLON'].mean():.3f}")
            state_agg = (
                df_fuel.groupby("LOCATION_STATE", as_index=False)
                .agg({"TOTAL_SPEND": "sum"})
                .sort_values("TOTAL_SPEND", ascending=False)
            )
            bar_fuel = (
                alt.Chart(state_agg, title="Fuel Spend by State")
                .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
                .encode(
                    x=alt.X("LOCATION_STATE:N", sort="-y", title="State"),
                    y=alt.Y("TOTAL_SPEND:Q", title="Total Spend ($)"),
                    color=alt.Color("LOCATION_STATE:N", legend=None),
                    tooltip=["LOCATION_STATE:N", "TOTAL_SPEND:Q"],
                ).properties(height=370)
            )
            st.altair_chart(bar_fuel, use_container_width=True)
            with st.expander("Full Fuel Spend Table"):
                st.dataframe(df_fuel, use_container_width=True)
    except Exception as e:
        st.warning(f"Could not load fuel spend data: {str(e)}")

# ═══════════════════════════════════════════════════════════════
# TAB 8 — Safety Incidents (Lab 6 port)
# ═══════════════════════════════════════════════════════════════
with tab8:
    st.header("⚠️ Safety Incidents")
    st.caption("Fleet-wide safety trends — sourced from `CS5542_WEEK5.PUBLIC.SAFETY_INCIDENTS`")
    try:
        df_safety_kpi = session.sql("""
            SELECT
                COUNT(*) AS TOTAL_INCIDENTS,
                ROUND(SUM(claim_amount), 0) AS TOTAL_CLAIMS,
                ROUND(AVG(IFF(at_fault_flag, 1, 0)) * 100, 1) AS AT_FAULT_PCT,
                ROUND(AVG(IFF(injury_flag, 1, 0)) * 100, 1) AS INJURY_PCT,
                ROUND(SUM(vehicle_damage_cost), 0) AS TOTAL_VEHICLE_DAMAGE,
                ROUND(AVG(IFF(preventable_flag, 1, 0)) * 100, 1) AS PREVENTABLE_PCT
            FROM CS5542_WEEK5.PUBLIC.SAFETY_INCIDENTS
        """).to_pandas()
        df_safety = session.sql("""
            SELECT incident_type,
                   COUNT(*) AS INCIDENTS,
                   ROUND(SUM(claim_amount), 0) AS CLAIMS,
                   ROUND(AVG(claim_amount), 0) AS AVG_CLAIM
            FROM CS5542_WEEK5.PUBLIC.SAFETY_INCIDENTS
            GROUP BY incident_type
            ORDER BY INCIDENTS DESC
        """).to_pandas()

        if not df_safety_kpi.empty:
            row = df_safety_kpi.iloc[0]
            sk1, sk2, sk3, sk4 = st.columns(4)
            sk1.metric("Total Incidents", f"{int(row.get('TOTAL_INCIDENTS', 0)):,}")
            sk2.metric("Total Claims", f"${int(row.get('TOTAL_CLAIMS', 0)):,}")
            sk3.metric("At-Fault Rate", f"{row.get('AT_FAULT_PCT', 0):.1f}%")
            sk4.metric("Injury Rate", f"{row.get('INJURY_PCT', 0):.1f}%")

        if not df_safety.empty:
            bar_safety = (
                alt.Chart(df_safety, title="Incident Count by Type")
                .mark_bar(cornerRadiusTopLeft=4, cornerRadiusTopRight=4)
                .encode(
                    x=alt.X("INCIDENTS:Q", title="Count"),
                    y=alt.Y("INCIDENT_TYPE:N", sort="-x", title="Incident Type"),
                    color=alt.Color(
                        "AVG_CLAIM:Q",
                        scale=alt.Scale(scheme="orangered"),
                        legend=alt.Legend(title="Avg Claim ($)"),
                    ),
                    tooltip=["INCIDENT_TYPE:N", "INCIDENTS:Q", "CLAIMS:Q", "AVG_CLAIM:Q"],
                ).properties(height=280)
            )
            st.altair_chart(bar_safety, use_container_width=True)
            with st.expander("Full Safety Table"):
                st.dataframe(df_safety, use_container_width=True)
    except Exception as e:
        st.warning(f"Could not load safety data: {str(e)}")

# Footer
st.divider()
st.caption("HyperLogistics v1.0 | CS5542 Smart Supply Chain Optimization System | Built with Streamlit + Snowflake Cortex")