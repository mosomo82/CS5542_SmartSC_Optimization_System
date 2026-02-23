import snowflake.snowpark as snowpark
import pandas as pd
import os

def ingest_bridges(session: snowflake.snowpark.Session, file_path: str) -> None:
    """
    Ingest National Bridge Inventory into Snowflake Bronze layer.
    """
    df = pd.read_csv(file_path)
    snow_df = session.create_dataframe(df)
    snow_df.write.mode("overwrite").save_as_table("BRONZE.BRIDGE_INVENTORY")

    print(f"Bridge inventory ingested from {file_path} to BRONZE.BRIDGE_INVENTORY")

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

    ingest_bridges(session, "data/NationalBridgeInventory.csv")