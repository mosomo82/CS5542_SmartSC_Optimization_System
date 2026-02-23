import snowflake.snowpark as snowpark
from snowflake.snowpark.functions import col, when, concat, lit

def preprocess_weather(session: snowflake.snowpark.Session) -> None:
    """
    Preprocess NOAA GSOD data to extract semantic weather alerts.
    Uses Cortex for text generation to create human-readable alerts.
    """
    # Load external table
    weather_df = session.table("BRONZE.NOAA_GSOD")

    # Extract alerts based on conditions
    alerts_df = weather_df.withColumn(
        "weather_alert",
        when(col("PRCP") > 50, "Heavy precipitation expected")
        .when(col("SNWD") > 10, "Significant snowfall")
        .when(col("VISIB") < 1, "Low visibility conditions")
        .otherwise("Normal conditions")
    ).withColumn(
        "alert_description",
        concat(
            lit("Station "), col("STATION"),
            lit(" reports "), col("weather_alert"),
            lit(" on "), col("DATE")
        )
    )

    # Save to Silver layer
    alerts_df.write.mode("overwrite").save_as_table("SILVER.WEATHER_ALERTS")

    print("NOAA weather preprocessing completed. Alerts saved to SILVER.WEATHER_ALERTS")

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

    preprocess_weather(session)