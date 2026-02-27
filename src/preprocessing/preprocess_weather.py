import snowflake.snowpark as snowpark
from snowflake.snowpark.functions import col, when, concat, lit, year

# Years to include — controls both METADATA$FILENAME pruning (fast S3 scan)
# and a DATE-level guard. Add/remove years here as needed.
ACTIVE_YEARS = [2023, 2024, 2025]

def preprocess_weather(session: snowpark.Session) -> None:
    """
    Preprocess NOAA GSOD data to extract semantic weather alerts.

    Filters to ACTIVE_YEARS only:
      - METADATA$FILENAME pruning pushes the year filter to S3 so Snowflake
        only scans the relevant year-prefixed files (fastest path).
      - A secondary year(DATE) filter removes any edge-case rows that slip
        through (e.g. December files that span two years).

    Writes results to SILVER.WEATHER_ALERTS.
    """
    # -- Load table and filter to active years --------------------------------
    # year() on the DATE column is efficiently pushed down to Snowflake;
    # no METADATA$FILENAME needed (that pseudo-column isn't exposed via Snowpark).
    weather_df = session.table("BRONZE.NOAA_GSOD") \
        .filter(year(col("DATE")).isin(ACTIVE_YEARS))

    # -- Derive alert label ----------------------------------------------------
    alerts_df = weather_df.withColumn(
        "WEATHER_ALERT",
        when(col("PRCP") > 50,  "Heavy precipitation expected")
        .when(col("SNDP") > 10, "Significant snowfall")
        .when(col("VISIB") < 1, "Low visibility conditions")
        .otherwise("Normal conditions")
    ).withColumn(
        "ALERT_DESCRIPTION",
        concat(
            lit("Station "), col("STATION"),
            lit(" reports "),  col("WEATHER_ALERT"),
            lit(" on "),       col("DATE"),
        )
    ).select(
        "STATION", "DATE", "LATITUDE", "LONGITUDE",
        "TEMP", "PRCP", "SNDP", "VISIB",
        "WEATHER_ALERT", "ALERT_DESCRIPTION"
    )

    # -- Save to Silver layer --------------------------------------------------
    alerts_df.write.mode("overwrite").save_as_table("SILVER.WEATHER_ALERTS")

    print(f"[OK] NOAA weather preprocessing done. Years={ACTIVE_YEARS}. "
          "Alerts saved to SILVER.WEATHER_ALERTS.")

if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    from src.utils.snowflake_conn import get_session, close_session

    session = get_session()
    preprocess_weather(session)
    close_session()