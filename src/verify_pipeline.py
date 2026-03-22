"""
verify_pipeline.py  –  Sanity-check every Bronze / Silver / Gold table
======================================================================
Run from the project root:
    python src/verify_pipeline.py

Logs row counts, expected minimums, and a PASS / FAIL for each table.
Also logs a few sample rows from any table that passes.

Lab 9 (Tony):
  - Replaced all print() calls with Python logging module.
  - Added schema assertions for all 4 SILVER tables:
      RISK_HEATMAP_VIEW, BRIDGE_INVENTORY_GEO,
      CLEANED_LOGISTICS, LOGISTICS_VECTORIZED.
    Each assertion verifies that the required columns exist and reports
    missing columns as an AssertionError (hard failure).
"""

import os
import sys
import logging
from pathlib import Path
from typing import Dict, List
from dotenv import load_dotenv
import snowflake.snowpark as snowpark

PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "src"))
load_dotenv(PROJECT_ROOT / ".env")

# ── logging setup ─────────────────────────────────────────────────────────────
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=log_level,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("verify_pipeline")


# ── expected minimum row counts per table ─────────────────────────────────────
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


# ── SILVER schema requirements (Lab 9 assertion gate) ─────────────────────────
# Maps each SILVER table to its required column names.
# Uses the actual normalized NBI column names for BRIDGE_INVENTORY_GEO.
SILVER_REQUIRED_COLUMNS: Dict[str, List[str]] = {
    "RISK_HEATMAP_VIEW": [
        "STATE",
        "CITY",
        "INCIDENT_COUNT",
        "AVG_SEVERITY",
        "_UPDATED_AT",
    ],
    "BRIDGE_INVENTORY_GEO": [
        "BRIDGE_ID",
        "LOCATION",             # GEOGRAPHY column built by preprocess_bridges.py
        "VERT_CLR_OVER_MT_053", # Vertical clearance — NBI normalized name
        "OPERATING_RATING_064", # Operating load rating — NBI normalized name
        "_PROCESSED_AT",
    ],
    "CLEANED_LOGISTICS": [
        "ORDER_ID",
        "ORDER_DATE",
        "SHIPPING_DATE",
        "DELIVERY_DATE",
        "SHIPPING_MODE",
        "LATE_DELIVERY_RISK",
        "DELAY_DAYS",
        "DELAY_PROPENSITY",
        "_INSERTED_AT",
    ],
    "LOGISTICS_VECTORIZED": [
        "CHUNK_ID",
        "RECORD_TYPE",
        "TEXT_CONTENT",
        "METADATA",
        "SOURCE_RECORD_IDS",
        "_VECTORIZED_AT",
    ],
}


# ── helpers ───────────────────────────────────────────────────────────────────

def _assert_silver_schema(session: snowpark.Session, table: str) -> None:
    """Assert that all required columns are present in a SILVER table.

    Queries INFORMATION_SCHEMA.COLUMNS to obtain the actual column list,
    then raises AssertionError listing any that are missing.

    Args:
        session: Active Snowpark session.
        table:   Table name (no schema prefix) — must be a key in
                 SILVER_REQUIRED_COLUMNS.

    Raises:
        AssertionError: If any required columns are absent from the table.
    """
    required = SILVER_REQUIRED_COLUMNS.get(table)
    if not required:
        return  # no schema spec for this table — skip

    sql = f"""
        SELECT COLUMN_NAME
        FROM HYPERLOGISTICS_DB.INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'SILVER'
          AND TABLE_NAME   = '{table}'
    """
    rows = session.sql(sql).collect()
    actual = {row["COLUMN_NAME"].upper() for row in rows}
    missing = [c for c in required if c.upper() not in actual]

    assert not missing, (
        f"Schema assertion FAILED for SILVER.{table}: "
        f"missing column(s): {missing}"
    )
    logger.info(
        "       Schema OK — SILVER.%s has all %d required column(s).",
        table, len(required),
    )


def check_table(session: snowpark.Session, schema: str, table: str, min_rows: int) -> bool:
    """Check row count for one table and run schema assertions for SILVER tables.

    Returns True if the row count meets the minimum threshold, False otherwise.
    Schema assertion failures are logged as errors but do not raise exceptions,
    so the verification run will complete all tables even if one schema fails.
    """
    full = f"HYPERLOGISTICS_DB.{schema}.{table}"
    try:
        count = session.sql(f"SELECT COUNT(*) AS CNT FROM {full}").collect()[0]["CNT"]
        status = "PASS" if count >= min_rows else "LOW "
        logger.info(
            "  [%s]  %-55s  %12s rows  (min: %s)",
            status, full, f"{count:,}", f"{min_rows:,}",
        )

        # ── schema assertion (SILVER only) ────────────────────────────────────
        if schema == "SILVER" and table in SILVER_REQUIRED_COLUMNS:
            try:
                _assert_silver_schema(session, table)
            except AssertionError as ae:
                logger.error("  [SCHEMA ERR]  %s", ae)
                return False

        # ── sample rows (non-empty tables, DEBUG level) ───────────────────────
        if count > 0:
            cols = (
                session.sql(f"SELECT * FROM {full} LIMIT 2")
                .to_pandas()
                .to_string(max_cols=6, max_colwidth=30)
            )
            for line in cols.splitlines():
                logger.debug("         %s", line)

        return count >= min_rows

    except Exception as exc:
        logger.error("  [ERR]   %-55s  %s", full, exc)
        return False


# ── main ──────────────────────────────────────────────────────────────────────

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


def main():
    session = build_session()

    logger.info("Snowflake account : %s", os.getenv("SNOWFLAKE_ACCOUNT"))
    logger.info("Database          : %s", os.getenv("SNOWFLAKE_DATABASE", "HYPERLOGISTICS_DB"))
    logger.info("=" * 80)

    total = 0
    passed = 0

    for schema, tables in TABLES.items():
        logger.info("── %s layer %s", schema, "─" * 60)
        for table, min_rows in tables.items():
            total += 1
            if check_table(session, schema, table, min_rows):
                passed += 1

    logger.info("=" * 80)
    logger.info("Result: %d/%d tables passed", passed, total)

    if passed < total:
        logger.warning("Some tables did not meet requirements.")
        logger.info("To re-run the full pipeline:  python src/run_pipeline.py")

    session.close()

    # Hard exit code so CI can catch failures
    if passed < total:
        sys.exit(1)


if __name__ == "__main__":
    main()
