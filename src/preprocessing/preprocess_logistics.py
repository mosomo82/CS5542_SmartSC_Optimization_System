import snowflake.snowpark as snowpark
from snowflake.snowpark.functions import (
    col, lit, concat, current_timestamp, object_construct,
    array_construct, udf
)
from snowflake.snowpark.types import StringType


# Templates for generating human-readable text per record type
TEXT_TEMPLATES = {
    "load": "Load {LOAD_ID}: {ORIGIN_CITY} → {DESTINATION_CITY}, {DISTANCE_MILES} miles, "
            "revenue ${REVENUE}, cost ${COST}, booking type: {BOOKING_TYPE}, status: {DELIVERY_STATUS}.",
    "trip": "Trip {TRIP_ID}: Driver {DRIVER_ID} in truck {TRUCK_ID}, "
            "{ORIGIN_CITY} → {DESTINATION_CITY}, {DISTANCE_MILES} miles on {EVENT_DATE}.",
    "fuel": "Fuel purchase: {FUEL_GALLONS} gal at ${FUEL_COST} for truck {TRUCK_ID} on {EVENT_DATE}.",
    "maintenance": "Maintenance for truck {TRUCK_ID}: {MAINTENANCE_TYPE}, cost ${MAINTENANCE_COST} on {EVENT_DATE}. "
                   "Notes: {DESCRIPTION}.",
    "safety": "Safety incident: {SAFETY_INCIDENT_TYPE} involving driver {DRIVER_ID} "
              "on {EVENT_DATE}. Details: {DESCRIPTION}.",
    "delivery": "Delivery for load {LOAD_ID}: Status {DELIVERY_STATUS}, "
                "on-time: {ON_TIME_FLAG}, detention: {DETENTION_MINUTES} min on {EVENT_DATE}.",
    "driver": "Driver {DRIVER_ID}: {DESCRIPTION}.",
    "truck": "Truck {TRUCK_ID}: {DESCRIPTION}.",
}

# Fallback template for record types not listed above
DEFAULT_TEMPLATE = "Record {RECORD_ID} ({RECORD_TYPE}): {DESCRIPTION}."


def preprocess_logistics(session: snowpark.Session) -> None:
    """
    Preprocess Logistics Operations data for RAG chatbot vectorization.

    Transforms raw BRONZE.LOGISTICS records into human-readable text chunks,
    then embeds them using Snowflake Cortex for semantic retrieval.
    Results are written to SILVER.LOGISTICS_VECTORIZED.
    """
    # Load raw data from Bronze layer
    raw_df = session.table("BRONZE.LOGISTICS")

    record_count = raw_df.count()
    print(f"Processing {record_count} records from BRONZE.LOGISTICS...")

    # Generate text content from structured fields
    # Using concat to build readable text for each record type
    text_df = raw_df.withColumn(
        "TEXT_CONTENT",
        concat(
            lit("Record type: "), col("RECORD_TYPE"), lit(". "),
            # Origin/destination if present
            concat(
                lit("Route: "),
                col("ORIGIN_CITY"), lit(" → "), col("DESTINATION_CITY"),
                lit(", "), col("DISTANCE_MILES"), lit(" miles. ")
            ),
            # Financial details if present
            concat(
                lit("Revenue: $"), col("REVENUE"),
                lit(", Cost: $"), col("COST"), lit(". ")
            ),
            # Status details
            concat(
                lit("Status: "), col("DELIVERY_STATUS"),
                lit(", On-time: "), col("ON_TIME_FLAG"), lit(". ")
            ),
            # Description
            concat(lit("Notes: "), col("DESCRIPTION"), lit("."))
        )
    )

    # Build metadata JSON for each record
    vectorized_df = text_df.select(
        col("RECORD_ID").alias("CHUNK_ID"),
        col("RECORD_TYPE"),
        col("TEXT_CONTENT"),
        object_construct(
            lit("route"), concat(col("ORIGIN_CITY"), lit(" → "), col("DESTINATION_CITY")),
            lit("driver_id"), col("DRIVER_ID"),
            lit("truck_id"), col("TRUCK_ID"),
            lit("event_date"), col("EVENT_DATE"),
            lit("revenue"), col("REVENUE"),
            lit("cost"), col("COST")
        ).alias("METADATA"),
        # Generate embedding using Snowflake Cortex
        # Note: Requires Cortex to be enabled on the account
        # snowflake.cortex.embed_text_768('snowflake-arctic-embed-m', TEXT_CONTENT)
        array_construct(col("RECORD_ID")).alias("SOURCE_RECORD_IDS")
    ).withColumn("_VECTORIZED_AT", current_timestamp())

    # Write to Silver layer
    vectorized_df.write.mode("overwrite").save_as_table("SILVER.LOGISTICS_VECTORIZED")

    print("Logistics Operations preprocessing complete.")
    print("   Output: SILVER.LOGISTICS_VECTORIZED")
    print("   Note: Run Cortex embedding separately to populate the EMBEDDING column:")
    print("         UPDATE SILVER.LOGISTICS_VECTORIZED")
    print("         SET EMBEDDING = SNOWFLAKE.CORTEX.EMBED_TEXT_768('snowflake-arctic-embed-m', TEXT_CONTENT);")


if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    from src.utils.snowflake_conn import get_session, close_session

    session = get_session()
    preprocess_logistics(session)
    close_session()
