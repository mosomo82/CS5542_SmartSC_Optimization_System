import re
import snowflake.snowpark
import snowflake.snowpark as snowpark
import pandas as pd
import os


def _normalize_col(c: str) -> str:
    """Normalize a CSV column name to a clean Snowflake identifier.
    Strips whitespace, uppercases, and replaces any run of non-alphanumeric
    characters with a single underscore, trimming leading/trailing underscores.
    """
    return re.sub(r'[^A-Z0-9]+', '_', c.strip().upper()).strip('_')

def ingest_bridges(session: snowflake.snowpark.Session, file_path: str) -> None:
    """
    Ingest National Bridge Inventory into Snowflake Bronze layer.
    """
    # low_memory=False prevents mixed-type inference warnings
    df = pd.read_csv(file_path, low_memory=False)

    # Normalize all column names to clean uppercase Snowflake identifiers
    df.columns = [_normalize_col(c) for c in df.columns]

    # PyArrow (used by Snowpark) fails on object columns with mixed str/int values.
    # Cast every object column to str; Snowflake casts them back on insert.
    for c in df.select_dtypes(include='object').columns:
        df[c] = df[c].astype(str)

    snow_df = session.create_dataframe(df)
    snow_df.write.mode("overwrite").save_as_table("BRONZE.BRIDGE_INVENTORY")

    print(f"Bridge inventory ingested from {file_path} to BRONZE.BRIDGE_INVENTORY "
          f"({len(df):,} rows)")

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

    ingest_bridges(session, "data/bridges/NTAD_National_Bridge_Inventory_-6282134062105639862.csv")