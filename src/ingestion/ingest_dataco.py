import re
import snowflake.snowpark
import snowflake.snowpark as snowpark
import pandas as pd
import os


def _normalize_col(c: str) -> str:
    """Normalize a CSV column name to a clean Snowflake identifier."""
    return re.sub(r'[^A-Z0-9]+', '_', c.strip().upper()).strip('_')

def ingest_dataco(session: snowflake.snowpark.Session, file_path: str) -> None:
    """
    Ingest DataCo Smart Supply Chain dataset into Snowflake Bronze layer.
    """
    # DataCo CSVs use Latin-1 encoding and have column names with spaces/parens.
    # Normalizing to clean uppercase identifiers ensures preprocessing scripts can
    # reference columns without quoted identifiers.
    df = pd.read_csv(file_path, encoding='latin1')
    df.columns = [_normalize_col(c) for c in df.columns]

    snow_df = session.create_dataframe(df)
    snow_df.write.mode("overwrite").save_as_table("BRONZE.RAW_LOGISTICS")

    print(f"DataCo dataset ingested from {file_path} to BRONZE.RAW_LOGISTICS "
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

    ingest_dataco(session, "data/dataco/DataCoSupplyChainDataset.csv")