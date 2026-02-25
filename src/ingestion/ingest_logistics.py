import snowflake.snowpark as snowpark
from snowflake.snowpark.functions import lit, current_timestamp
import pandas as pd
import os
from pathlib import Path


# Mapping of source CSV files to their record_type tag
LOGISTICS_TABLES = {
    "loads.csv":              "load",
    "trips.csv":              "trip",
    "drivers.csv":            "driver",
    "trucks.csv":             "truck",
    "trailers.csv":           "trailer",
    "customers.csv":          "customer",
    "facilities.csv":         "facility",
    "routes.csv":             "route",
    "fuel_purchases.csv":     "fuel",
    "maintenance_records.csv": "maintenance",
    "delivery_events.csv":    "delivery",
    "safety_incidents.csv":   "safety",
    "driver_monthly_metrics.csv":  "driver_metric",
    "truck_utilization_metrics.csv": "truck_metric",
}

# Column mapping: normalize diverse CSV columns to unified Bronze schema
COLUMN_MAP = {
    "load_id":               "LOAD_ID",
    "trip_id":               "TRIP_ID",
    "driver_id":             "DRIVER_ID",
    "truck_id":              "TRUCK_ID",
    "trailer_id":            "TRAILER_ID",
    "customer_id":           "CUSTOMER_ID",
    "facility_id":           "FACILITY_ID",
    "route_id":              "ROUTE_ID",
    "origin_city":           "ORIGIN_CITY",
    "destination_city":      "DESTINATION_CITY",
    "distance_miles":        "DISTANCE_MILES",
    "revenue":               "REVENUE",
    "total_cost":            "COST",
    "cost":                  "COST",
    "fuel_gallons":          "FUEL_GALLONS",
    "fuel_cost":             "FUEL_COST",
    "maintenance_type":      "MAINTENANCE_TYPE",
    "service_type":          "MAINTENANCE_TYPE",
    "maintenance_cost":      "MAINTENANCE_COST",
    "delivery_status":       "DELIVERY_STATUS",
    "status":                "DELIVERY_STATUS",
    "on_time":               "ON_TIME_FLAG",
    "detention_minutes":     "DETENTION_MINUTES",
    "incident_type":         "SAFETY_INCIDENT_TYPE",
    "booking_type":          "BOOKING_TYPE",
    "event_date":            "EVENT_DATE",
    "date":                  "EVENT_DATE",
    "event_timestamp":       "EVENT_TIMESTAMP",
    "timestamp":             "EVENT_TIMESTAMP",
    "description":           "DESCRIPTION",
    "notes":                 "DESCRIPTION",
}


# Target Snowflake table schema (28 columns)
UNIFIED_SCHEMA = [
    "RECORD_ID", "RECORD_TYPE", "LOAD_ID", "TRIP_ID", "DRIVER_ID", "TRUCK_ID",
    "TRAILER_ID", "CUSTOMER_ID", "FACILITY_ID", "ROUTE_ID", "ORIGIN_CITY",
    "DESTINATION_CITY", "DISTANCE_MILES", "REVENUE", "COST", "FUEL_GALLONS",
    "FUEL_COST", "MAINTENANCE_TYPE", "MAINTENANCE_COST", "DELIVERY_STATUS",
    "ON_TIME_FLAG", "DETENTION_MINUTES", "SAFETY_INCIDENT_TYPE", "BOOKING_TYPE",
    "EVENT_DATE", "EVENT_TIMESTAMP", "DESCRIPTION"
]


def ingest_logistics(session: snowpark.Session, data_dir: str) -> None:
    """
    Ingest the Logistics Operations Database into Snowflake Bronze layer.

    Reads 14 CSV files from the dataset, tags each with a RECORD_TYPE,
    normalizes columns to a unified schema, and loads into BRONZE.LOGISTICS.

    Args:
        session: Active Snowpark session
        data_dir: Path to directory containing the Logistics Operations CSV files
    """
    data_path = Path(data_dir)
    total_records = 0

    for csv_file, record_type in LOGISTICS_TABLES.items():
        file_path = data_path / csv_file
        if not file_path.exists():
            print(f"  ⚠ Skipping {csv_file} (not found)")
            continue

        print(f"  📥 Ingesting {csv_file} as record_type='{record_type}'...")

        # Read CSV and normalize column names
        df = pd.read_csv(file_path)
        df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

        # Create a unified row structure
        unified = pd.DataFrame()
        unified["RECORD_TYPE"] = record_type

        # Map available columns to unified schema
        for src_col, tgt_col in COLUMN_MAP.items():
            if src_col in df.columns and tgt_col not in unified.columns:
                unified[tgt_col] = df[src_col]

        # Generate a unique record ID
        unified["RECORD_ID"] = [
            f"{record_type}_{i}" for i in range(len(df))
        ]

        # CRITICAL FIX: Ensure ALL columns from the table schema exist in the DF
        # This prevents the "expected 28 but got 8" SQL error
        for col_name in UNIFIED_SCHEMA:
            if col_name not in unified.columns:
                unified[col_name] = None

        # Reorder to match Snowflake table order exactly
        unified = unified[UNIFIED_SCHEMA]

        # Convert date/time columns to proper types to avoid Snowflake type mismatch errors
        if "EVENT_DATE" in unified.columns:
            unified["EVENT_DATE"] = pd.to_datetime(unified["EVENT_DATE"]).dt.date
        if "EVENT_TIMESTAMP" in unified.columns:
            unified["EVENT_TIMESTAMP"] = pd.to_datetime(unified["EVENT_TIMESTAMP"])

        # Upload to Snowflake in chunks
        chunk_size = 50000
        for start in range(0, len(unified), chunk_size):
            chunk = unified.iloc[start:start + chunk_size]
            snow_df = session.create_dataframe(chunk)
            # Snowflake will automatically handle the 28th column (_INGESTED_AT) if we define it here:
            snow_df = snow_df.withColumn("_INGESTED_AT", current_timestamp())
            snow_df.write.mode("append").save_as_table("BRONZE.LOGISTICS")

        total_records += len(unified)
        print(f"    ✅ {len(unified)} records loaded")

    print(f"\n📊 Logistics Operations ingestion complete: {total_records} total records → BRONZE.LOGISTICS")


if __name__ == "__main__":
    from dotenv import load_dotenv
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

    # Default path assumes dataset is extracted to data/logistics/
    ingest_logistics(session, "data/logistics")
