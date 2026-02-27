import snowflake.snowpark as snowpark
from snowflake.snowpark.functions import col, st_geogfromtext, concat, lit

def preprocess_bridges(session: snowpark.Session) -> None:
    """
    Preprocess National Bridge Inventory to enable spatial joins.
    Converts lat/lon to GEOGRAPHY type for compliance checks.
    """
    # Load raw bridge data
    bridges_df = session.table("BRONZE.BRIDGE_INVENTORY")

    # The NTAD NBI export provides LATDD / LONGDD as clean decimal-degree columns.
    # These names are stable after the column-normalization applied in ingest_bridges.py.
    geo_bridges = bridges_df.withColumn(
        "LOCATION",
        st_geogfromtext(concat(lit("POINT("), col("LONGDD"), lit(" "), col("LATDD"), lit(")")))
    )

    # Save to Silver layer
    geo_bridges.write.mode("overwrite").save_as_table("SILVER.BRIDGE_INVENTORY_GEO")

    print("Bridge inventory preprocessing completed. Geography data saved.")

if __name__ == "__main__":
    import sys, os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))
    from src.utils.snowflake_conn import get_session, close_session

    session = get_session()
    preprocess_bridges(session)
    close_session()