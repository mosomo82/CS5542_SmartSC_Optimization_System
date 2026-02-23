import snowflake.snowpark as snowpark
from snowflake.snowpark.functions import col, st_geogfromtext, concat

def preprocess_bridges(session: snowflake.snowpark.Session) -> None:
    """
    Preprocess National Bridge Inventory to enable spatial joins.
    Converts lat/lon to GEOGRAPHY type for compliance checks.
    """
    # Load raw bridge data
    bridges_df = session.table("BRONZE.BRIDGE_INVENTORY")

    # Convert to geography
    geo_bridges = bridges_df.withColumn(
        "location",
        st_geogfromtext(concat(lit("POINT("), col("longitude"), lit(" "), col("latitude"), lit(")")))
    )

    # Save to Silver layer
    geo_bridges.write.mode("overwrite").save_as_table("SILVER.BRIDGE_INVENTORY_GEO")

    print("Bridge inventory preprocessing completed. Geography data saved.")

if __name__ == "__main__":
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

    preprocess_bridges(session)