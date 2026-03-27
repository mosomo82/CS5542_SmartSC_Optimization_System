"""
run_pipeline.py  –  Full Bronze → Silver → Gold pipeline runner
================================================================
Run from the project root:
    python src/run_pipeline.py

Requires a .env file at the project root (copy .env.template → .env).
The SQL schema must already exist  (run src/sql/00_create_database.sql in Snowflake first).

Steps executed (in order):
  1. Ingest: Accidents  → BRONZE.TRAFFIC_INCIDENTS
  2. Ingest: Bridges    → BRONZE.BRIDGE_INVENTORY
  3. Ingest: DataCo     → BRONZE.RAW_LOGISTICS
  4. Ingest: Logistics  → BRONZE.LOGISTICS
  5. Preprocess: Accidents  → SILVER.RISK_HEATMAP_VIEW
  6. Preprocess: Bridges    → SILVER.BRIDGE_INVENTORY_GEO
  7. Preprocess: DataCo     → SILVER.CLEANED_LOGISTICS
  8. Preprocess: Logistics  → SILVER.LOGISTICS_VECTORIZED

Lab 9: replaced all print() calls with Python logging module.
"""

import os
import sys
import logging
import traceback
from pathlib import Path

# ── resolve project root so relative imports work wherever you invoke this ──
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

# ── logging setup ─────────────────────────────────────────────────────────────
log_level = os.getenv("LOG_LEVEL", "INFO").upper()
logging.basicConfig(
    level=log_level,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger("run_pipeline")

from src.utils.snowflake_conn import get_session, close_session


# ── helpers ───────────────────────────────────────────────────────────────────
def _step(label: str, fn, *args, **kwargs):
    """Run one pipeline step, log result, continue on non-fatal errors."""
    logger.info("─" * 60)
    logger.info("[STEP] %s", label)
    try:
        fn(*args, **kwargs)
        logger.info("[OK] %s completed.", label)
    except Exception as exc:
        logger.warning("[WARN] %s FAILED — pipeline will continue.\n  %s", label, exc)
        logger.debug(traceback.format_exc())


# ── main ──────────────────────────────────────────────────────────────────────
def main():
    data_dir = PROJECT_ROOT / "data"

    session = get_session()

    # ── Bronze ingestion ──────────────────────────────────────────────────────
    from ingestion.ingest_accidents import ingest_accidents
    from ingestion.ingest_bridges   import ingest_bridges
    from ingestion.ingest_dataco    import ingest_dataco
    from ingestion.ingest_logistics import ingest_logistics

    _step(
        "Ingest Accidents → BRONZE.TRAFFIC_INCIDENTS",
        ingest_accidents,
        session,
        str(data_dir / "accidents" / "US_Accidents_March23.csv"),
    )

    _step(
        "Ingest Bridges → BRONZE.BRIDGE_INVENTORY",
        ingest_bridges,
        session,
        str(data_dir / "bridges" / "NTAD_National_Bridge_Inventory_-6282134062105639862.csv"),
    )

    _step(
        "Ingest DataCo → BRONZE.RAW_LOGISTICS",
        ingest_dataco,
        session,
        str(data_dir / "dataco" / "DataCoSupplyChainDataset.csv"),
    )

    _step(
        "Ingest Logistics Ops → BRONZE.LOGISTICS",
        ingest_logistics,
        session,
        str(data_dir / "logistics"),
    )

    # ── Silver preprocessing ──────────────────────────────────────────────────
    from preprocessing.preprocess_accidents import preprocess_accidents
    from preprocessing.preprocess_bridges   import preprocess_bridges
    from preprocessing.preprocess_dataco    import preprocess_dataco
    from preprocessing.preprocess_logistics import preprocess_logistics

    _step(
        "Preprocess Accidents → SILVER.RISK_HEATMAP_VIEW",
        preprocess_accidents,
        session,
    )

    _step(
        "Preprocess Bridges → SILVER.BRIDGE_INVENTORY_GEO",
        preprocess_bridges,
        session,
    )

    _step(
        "Preprocess DataCo → SILVER.CLEANED_LOGISTICS",
        preprocess_dataco,
        session,
    )

    _step(
        "Preprocess Logistics → SILVER.LOGISTICS_VECTORIZED",
        preprocess_logistics,
        session,
    )

    logger.info("═" * 60)
    logger.info("[DONE] Pipeline finished. Check Snowflake for data in BRONZE / SILVER.")
    logger.info("═" * 60)

    close_session()


if __name__ == "__main__":
    main()
