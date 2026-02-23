import snowflake.snowpark as snowpark
from snowflake.snowpark.functions import col, datediff, avg, when
import pandas as pd

def preprocess_dataco(session: snowflake.snowpark.Session) -> None:
    """
    Preprocess the DataCo Smart Supply Chain dataset.
    Calculates delay propensity scores and prepares for SRSNet training.
    """
    # Load raw data from Bronze layer
    raw_df = session.table("BRONZE.RAW_LOGISTICS")

    # Feature engineering: Calculate delay propensity
    processed_df = raw_df.withColumn(
        "delay_days",
        datediff("day", col("order_date"), col("shipping_date"))
    ).withColumn(
        "late_delivery_risk_score",
        when(col("late_delivery_risk") == "Yes", 1).otherwise(0)
    ).withColumn(
        "delay_propensity",
        avg("delay_days").over("shipping_mode")  # Rolling average by shipping mode
    )

    # Save to Silver layer
    processed_df.write.mode("overwrite").save_as_table("SILVER.CLEANED_LOGISTICS")

    print("DataCo preprocessing completed. Data saved to SILVER.CLEANED_LOGISTICS")

if __name__ == "__main__":
    # For local testing (requires Snowflake connection)
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

    preprocess_dataco(session)