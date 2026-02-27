import snowflake.snowpark as snowpark
from snowflake.snowpark.functions import col, avg, cast
from snowflake.snowpark.types import IntegerType
from snowflake.snowpark import Window

def preprocess_dataco(session: snowpark.Session) -> None:
    """
    Preprocess the DataCo Smart Supply Chain dataset.
    Calculates delay propensity scores and prepares for SRSNet training.

    Column names reflect the normalization applied in ingest_dataco.py:
      "Days for shipping (real)"       → DAYS_FOR_SHIPPING_REAL
      "Days for shipment (scheduled)" → DAYS_FOR_SHIPMENT_SCHEDULED
      "Late_delivery_risk"             → LATE_DELIVERY_RISK  (0/1 integer)
      "Shipping Mode"                  → SHIPPING_MODE
    """
    # Load raw data from Bronze layer
    raw_df = session.table("BRONZE.RAW_LOGISTICS")

    # Feature engineering
    # delay_days: how many extra days beyond scheduled (positive = late)
    # LATE_DELIVERY_RISK is already 0/1 in the DataCo dataset
    processed_df = raw_df.withColumn(
        "DELAY_DAYS",
        col("DAYS_FOR_SHIPPING_REAL") - col("DAYS_FOR_SHIPMENT_SCHEDULED")
    ).withColumn(
        "LATE_DELIVERY_RISK_SCORE",
        cast(col("LATE_DELIVERY_RISK"), IntegerType())
    ).withColumn(
        "DELAY_PROPENSITY",
        avg(col("DAYS_FOR_SHIPPING_REAL")).over(Window.partitionBy(col("SHIPPING_MODE")))
    )

    # Save to Silver layer
    processed_df.write.mode("overwrite").save_as_table("SILVER.CLEANED_LOGISTICS")

    print("DataCo preprocessing completed. Data saved to SILVER.CLEANED_LOGISTICS")

if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    from src.utils.snowflake_conn import get_session, close_session

    session = get_session()
    preprocess_dataco(session)
    close_session()