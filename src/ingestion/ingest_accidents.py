import snowflake.snowpark as snowpark
import pandas as pd
import os

def ingest_accidents(session: snowflake.snowpark.Session, file_path: str) -> None:
    """
    Ingest US Accidents dataset into Snowflake Bronze layer.
    Handles large file with chunking.
    """
    # Read in chunks to handle 3GB file
    chunk_size = 100000
    for chunk in pd.read_csv(file_path, chunksize=chunk_size):
        snow_df = session.create_dataframe(chunk)
        snow_df.write.mode("append").save_as_table("BRONZE.TRAFFIC_INCIDENTS")

    print(f"US Accidents dataset ingested from {file_path} to BRONZE.TRAFFIC_INCIDENTS")

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

    ingest_accidents(session, "data/US_Accidents_March23.csv")