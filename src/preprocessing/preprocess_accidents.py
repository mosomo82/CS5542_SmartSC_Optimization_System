import snowflake.snowpark as snowpark
from snowflake.snowpark.functions import col, count, avg, window

def preprocess_accidents(session: snowpark.Session) -> None:
    """
    Preprocess US Accidents dataset to create risk heatmap view.
    Aggregates incidents by location and time for efficient querying.
    """
    # Column names are normalized to uppercase by ingest_accidents.py:
    #   Start_Time → START_TIME,  State → STATE,  City → CITY,  Severity → SEVERITY
    accidents_df = session.table("BRONZE.TRAFFIC_INCIDENTS")

    # Create risk heatmap: Aggregate by state, city, and hour
    risk_heatmap = accidents_df.withColumn("HOUR", col("START_TIME").substr(0, 13)) \
        .groupBy(col("STATE"), col("CITY"), col("HOUR")) \
        .agg(
            count("*").alias("INCIDENT_COUNT"),
            avg("SEVERITY").alias("AVG_SEVERITY")
        )

    # Save as view for fast access
    risk_heatmap.create_or_replace_view("SILVER.RISK_HEATMAP_VIEW")

    print("US Accidents preprocessing completed. Risk heatmap view created.")

if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    from src.utils.snowflake_conn import get_session, close_session

    session = get_session()
    preprocess_accidents(session)
    close_session()