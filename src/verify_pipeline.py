"""
verify_pipeline.py  –  Sanity-check every Bronze / Silver / Gold table
======================================================================
Run from the project root:
    python src/verify_pipeline.py

Prints row counts, expected minimums, and a PASS / FAIL for each table.
Also prints a few sample rows from any table that passes.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv
import snowflake.snowpark as snowpark

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
load_dotenv(PROJECT_ROOT / ".env")


# ── expected minimum row counts per table ────────────────────────────────────
TABLES = {
    # layer           table name                       min rows expected
    "BRONZE": {
        "TRAFFIC_INCIDENTS":    3_000_000,   # US Accidents March23 snapshot ~3.2M rows
        "BRIDGE_INVENTORY":     600_000,     # NBI ~620K bridges
        "RAW_LOGISTICS":        100_000,     # DataCo ~180K orders
        "LOGISTICS":            80_000,      # Logistics Ops DB ~85K records
    },
    "SILVER": {
        "RISK_HEATMAP_VIEW":    1,           # view – just needs to exist
        "BRIDGE_INVENTORY_GEO": 600_000,
        "CLEANED_LOGISTICS":    100_000,
        "LOGISTICS_VECTORIZED": 1,
    },
    "GOLD": {
        "VECTOR_EMBEDDINGS":    0,           # populated separately
        "DISRUPTION_REPORTS":   0,
        "QUERY_LOGS":           0,
    },
}


def build_session() -> snowpark.Session:
    return snowpark.Session.builder.configs({
        "account":   os.getenv("SNOWFLAKE_ACCOUNT"),
        "user":      os.getenv("SNOWFLAKE_USER"),
        "password":  os.getenv("SNOWFLAKE_PASSWORD"),
        "role":      os.getenv("SNOWFLAKE_ROLE"),
        "warehouse": os.getenv("SNOWFLAKE_WAREHOUSE"),
        "database":  os.getenv("SNOWFLAKE_DATABASE", "HYPERLOGISTICS_DB"),
        "schema":    "PUBLIC",
    }).create()


def check_table(session, schema: str, table: str, min_rows: int) -> bool:
    full = f"HYPERLOGISTICS_DB.{schema}.{table}"
    try:
        count = session.sql(f"SELECT COUNT(*) AS CNT FROM {full}").collect()[0]["CNT"]
        status = "✅ PASS" if count >= min_rows else "⚠️  LOW "
        print(f"  {status}  {full:<55} {count:>12,} rows  (min: {min_rows:,})")

        # show 2 sample rows for non-empty tables
        if count > 0:
            cols = session.sql(
                f"SELECT * FROM {full} LIMIT 2"
            ).to_pandas().to_string(max_cols=6, max_colwidth=30)
            for line in cols.splitlines():
                print(f"         {line}")
        return count >= min_rows

    except Exception as exc:
        print(f"  ❌ ERR   {full:<55} {exc}")
        return False


def main():
    session = build_session()
    print(f"\nSnowflake account : {os.getenv('SNOWFLAKE_ACCOUNT')}")
    print(f"Database          : {os.getenv('SNOWFLAKE_DATABASE', 'HYPERLOGISTICS_DB')}")
    print("=" * 80)

    total = 0
    passed = 0

    for schema, tables in TABLES.items():
        print(f"\n── {schema} layer ──────────────────────────────────────────────────────────")
        for table, min_rows in tables.items():
            total += 1
            if check_table(session, schema, table, min_rows):
                passed += 1

    print("\n" + "=" * 80)
    print(f"Result: {passed}/{total} tables passed")

    if passed < total:
        print("\nTo re-run the full pipeline:  py src/run_pipeline.py")

    session.close()


if __name__ == "__main__":
    main()
