import streamlit as st
import snowflake.snowpark as snowpark
import pandas as pd
import folium
from streamlit_folium import folium_static
from dotenv import load_dotenv
import os

# Load environment
load_dotenv()

# Snowflake connection
@st.cache_resource
def get_session():
    return snowpark.Session.builder.configs({
        "account": os.getenv("SNOWFLAKE_ACCOUNT"),
        "user": os.getenv("SNOWFLAKE_USER"),
        "password": os.getenv("SNOWFLAKE_PASSWORD"),
        "role": os.getenv("SNOWFLAKE_ROLE"),
        "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
        "database": os.getenv("SNOWFLAKE_DATABASE"),
        "schema": os.getenv("SNOWFLAKE_SCHEMA")
    }).create()

session = get_session()

st.title("HyperLogistics: Smart Supply Chain Optimization Dashboard")

# Sidebar for queries
st.sidebar.header("Ask the Agent")
query = st.sidebar.text_input("Enter your logistics query:")

if st.sidebar.button("Submit Query"):
    # Placeholder for RAG/Cortex response
    response = "Based on current weather data, reroute via I-55 to avoid delays."
    st.sidebar.success(response)

# Main dashboard
st.header("Risk Heatmap")
# Placeholder map
m = folium.Map(location=[39.8283, -98.5795], zoom_start=4)
folium_static(m)

st.header("Route Comparison")
# Placeholder comparison
col1, col2 = st.columns(2)
with col1:
    st.subheader("Original Route")
    st.write("Route A: Chicago → St. Louis → Kansas City")
    st.write("Estimated delay: 4 hours")

with col2:
    st.subheader("AI-Suggested Route")
    st.write("Route B: Chicago → Indianapolis → Kansas City")
    st.write("Estimated delay: 1 hour")

st.header("Reasoning Path")
st.write("**Evidence:** NOAA data shows severe weather on I-70. Historical accidents indicate 85% higher risk during snow events.")

if __name__ == "__main__":
    st.write("Dashboard loaded successfully.")