import re
import snowflake.snowpark
import snowflake.snowpark as snowpark
import pandas as pd
import os


def _normalize_col(c: str) -> str:
    """Normalize a CSV column name to a clean Snowflake identifier."""
    return re.sub(r'[^A-Z0-9]+', '_', c.strip().upper()).strip('_')


def ingest_accidents(session: snowflake.snowpark.Session, file_path: str) -> None:
    """
    Ingest US Accidents dataset into Snowflake Bronze layer.
    Handles large file with chunking.
    """
    # Drop and recreate so the table schema is driven by the actual CSV,
    # not the DDL stub (which has a different column count).
    # save_as_table(overwrite) only does DELETE+INSERT on an existing table,
    # so we must DROP explicitly first.
    session.sql("DROP TABLE IF EXISTS BRONZE.TRAFFIC_INCIDENTS").collect()

    chunk_size = 100000
    total = 0
    for chunk in pd.read_csv(file_path, chunksize=chunk_size, low_memory=False):
        # Normalize all column names to clean uppercase identifiers
        chunk.columns = [_normalize_col(c) for c in chunk.columns]

        # Always append — after the DROP the first chunk creates the table
        session.create_dataframe(chunk).write.mode("append").save_as_table(
            "BRONZE.TRAFFIC_INCIDENTS"
        )
        total += len(chunk)
        print(f"    ... {total:,} rows loaded", end="\r")

    print(f"\nUS Accidents dataset ingested from {file_path} to BRONZE.TRAFFIC_INCIDENTS "
          f"({total:,} rows)")

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

    ingest_accidents(session, "data/accidents/US_Accidents_March23.csv")