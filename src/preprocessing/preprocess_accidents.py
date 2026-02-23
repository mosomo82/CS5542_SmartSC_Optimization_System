import snowflake.snowpark as snowpark
from snowflake.snowpark.functions import col, count, avg, window

def preprocess_accidents(session: snowflake.snowpark.Session) -> None:
    """
    Preprocess US Accidents dataset to create risk heatmap view.
    Aggregates incidents by location and time for efficient querying.
    """
    # Load raw accidents data
    accidents_df = session.table("BRONZE.TRAFFIC_INCIDENTS")

    # Create risk heatmap: Aggregate by state, city, and hour
    risk_heatmap = accidents_df.groupBy(
        col("State"), col("City"), col("Start_Time").substr(0, 13)  # Hour level
    ).agg(
        count("*").alias("incident_count"),
        avg("Severity").alias("avg_severity")
    ).withColumnRenamed("substr(Start_Time, 0, 13)", "hour")

    # Save as view for fast access
    risk_heatmap.create_or_replace_view("SILVER.RISK_HEATMAP_VIEW")

    print("US Accidents preprocessing completed. Risk heatmap view created.")

if __name__ == "__main__":
    from dotenv import load_dotenv
    import os
    load_dotenv()

    session = snowpark.Session.builder.configs({
        "account": os.getenv("SNOWFLAKE_ACCOUNT"),
        "user": os.getenv("SNOWFLAKE_USER"),
        "password": os.getenv("SNOWFLAKE_PASSWORD"),
        "role": os.getenv("SNOWFLAKE_ROLE"),
        "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
        "database": os.getenv("SNOWFLAKE_DATABASE"),
        "schema": os.getenv("SNOWFLAKE_SCHEMA")
    }).create()

    preprocess_accidents(session)