import snowflake.snowpark as snowpark
import pandas as pd
import os

def ingest_dataco(session: snowflake.snowpark.Session, file_path: str) -> None:
    """
    Ingest DataCo Smart Supply Chain dataset into Snowflake Bronze layer.
    """
    # Read CSV (assuming local file for demo; in practice, upload to stage first)
    df = pd.read_csv(file_path)

    # Convert to Snowpark DataFrame
    snow_df = session.create_dataframe(df)

    # Save to Bronze table
    snow_df.write.mode("overwrite").save_as_table("BRONZE.RAW_LOGISTICS")

    print(f"DataCo dataset ingested from {file_path} to BRONZE.RAW_LOGISTICS")

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

    # Example usage: ingest_dataco(session, "data/DataCoSupplyChainDataset.csv")
    ingest_dataco(session, "data/DataCoSupplyChainDataset.csv")