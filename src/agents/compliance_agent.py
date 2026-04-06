"""
compliance_agent.py — CPP Step 3A: Spatial SQL Hard Gate
=========================================================
Implements the Compliance Pre-Processing (CPP) Step 3A hard-veto gate.

Before any LLM call, this agent queries Snowflake's SILVER.BRIDGE_INVENTORY_GEO
using ST_INTERSECTS to find all bridges a proposed route passes over or under,
then computes the minimum weight and clearance margins.

If ANY bridge on the route would be:
  - Over the vehicle's weight limit  (OPERATING_RATING_064 < vehicle_weight_tons)
  - Under the vehicle's height       (VERT_CLR_OVER_MT_053 < vehicle_height_mt)

...a HARD VETO is issued and the pipeline stops immediately — no LLM is called.

Usage:
    from src.agents.compliance_agent import check_route_compliance, ComplianceResult

    result = check_route_compliance(
        session=session,
        route_wkt="LINESTRING(-87.6298 41.8781, -90.1994 38.6270)",
        vehicle_weight_tons=40.0,
        vehicle_height_mt=4.5,
    )
    if result.verdict == "HARD_VETO":
        return result.veto_reason  # stop, no LLM call
"""

import logging
from dataclasses import dataclass, field
from typing import Any, List

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Result dataclass
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class ComplianceResult:
    """Outcome of the CPP Step 3A spatial hard-gate check.

    Attributes:
        verdict:              "PASS" or "HARD_VETO"
        failing_bridges:      List of dicts describing each non-compliant bridge
                              (keys: bridge_id, clearance_mt, weight_limit_tons,
                               weight_margin, clearance_margin).
        min_weight_margin:    MIN(weight_limit_tons / vehicle_weight_tons) across
                              ALL intersecting bridges. Value < 1.0 means veto.
                              None if no bridges intersect the route.
        min_clearance_margin: MIN(clearance_mt - vehicle_height_mt) across ALL
                              intersecting bridges. Negative value means veto.
                              None if no bridges intersect the route.
        veto_reason:          Human-readable explanation when verdict == "HARD_VETO".
                              Empty string when verdict == "PASS".
        intersecting_count:   Total number of bridges the route passes through.
    """
    verdict: str                        # "PASS" | "HARD_VETO"
    failing_bridges: List[dict] = field(default_factory=list)
    min_weight_margin: float | None = None
    min_clearance_margin: float | None = None
    veto_reason: str = ""
    intersecting_count: int = 0


# ─────────────────────────────────────────────────────────────────────────────
# Core gate function
# ─────────────────────────────────────────────────────────────────────────────

# SQL that finds all bridges whose LOCATION geometry intersects the route,
# computes per-bridge margins, and returns only violating rows plus aggregates.
#
# Column name notes (real NBI-normalized names in SILVER.BRIDGE_INVENTORY_GEO):
#   VERT_CLR_OVER_MT_053  — Vertical clearance above the road deck (metres)
#   OPERATING_RATING_064  — Operating (load) rating in tons
#   LATDD / LONGDD / LOCATION — Geography column built by preprocess_bridges.py

_SQL_SPATIAL_GATE = """
SELECT
    STRUCTURE_NUMBER_008                                    AS bridge_id,
    VERT_CLR_OVER_MT_053                                    AS clearance_mt,
    OPERATING_RATING_064                                    AS weight_limit_tons,
    OPERATING_RATING_064 / NULLIF({vehicle_weight}, 0)      AS weight_margin,
    VERT_CLR_OVER_MT_053 - {vehicle_height}                 AS clearance_margin
FROM HYPERLOGISTICS_DB.SILVER.BRIDGE_INVENTORY_GEO
WHERE
    ST_INTERSECTS(LOCATION, TO_GEOGRAPHY('{route_wkt}'))
    AND (
          OPERATING_RATING_064 < {vehicle_weight}
       OR VERT_CLR_OVER_MT_053 < {vehicle_height}
    )
ORDER BY weight_margin ASC NULLS LAST
LIMIT 50
"""

# Separate aggregate query — returns one row with min margins + total count
# across ALL intersecting bridges (not just failing ones), for the margin
# summary fields of ComplianceResult.
_SQL_AGGREGATE = """
SELECT
    COUNT(*)                                                    AS intersecting_count,
    MIN(OPERATING_RATING_064 / NULLIF({vehicle_weight}, 0))    AS min_weight_margin,
    MIN(VERT_CLR_OVER_MT_053 - {vehicle_height})               AS min_clearance_margin
FROM HYPERLOGISTICS_DB.SILVER.BRIDGE_INVENTORY_GEO
WHERE ST_INTERSECTS(LOCATION, TO_GEOGRAPHY('{route_wkt}'))
"""


def check_route_compliance(
    session: Any,
    route_wkt: str,
    vehicle_weight_tons: float,
    vehicle_height_mt: float,
) -> ComplianceResult:
    """CPP Step 3A: run the spatial SQL hard gate and return a ComplianceResult.

    This is the **FIRST** function called in the CPP pipeline. If it returns
    verdict == "HARD_VETO", the caller must stop immediately and NOT invoke any
    LLM or further routing logic.

    Args:
        session:             Active Snowflake Snowpark Session.
        route_wkt:           WKT LINESTRING geometry of the proposed route, e.g.
                             "LINESTRING(-87.6298 41.8781, -90.1994 38.6270)".
        vehicle_weight_tons: Gross vehicle weight in short tons.
        vehicle_height_mt:   Vehicle height in metres.

    Returns:
        ComplianceResult with verdict "PASS" or "HARD_VETO".
    """
    logger.info(
        "[CPP Gate 3A] Checking compliance: weight=%.1f tons, height=%.2f m | route=%s…",
        vehicle_weight_tons, vehicle_height_mt, route_wkt[:60],
    )

    # ── Step 1: Find violating bridges via ST_INTERSECTS ──────────────────────
    veto_sql = _SQL_SPATIAL_GATE.format(
        route_wkt=route_wkt.replace("'", "\\'"),
        vehicle_weight=vehicle_weight_tons,
        vehicle_height=vehicle_height_mt,
    )
    try:
        veto_rows = session.sql(veto_sql).collect()
    except Exception as exc:
        logger.error("[CPP Gate 3A] Spatial veto query failed: %s", exc)
        raise

    failing_bridges = [
        {
            "bridge_id":         str(row["BRIDGE_ID"]),
            "clearance_mt":      float(row["CLEARANCE_MT"]) if row["CLEARANCE_MT"] is not None else None,
            "weight_limit_tons": float(row["WEIGHT_LIMIT_TONS"]) if row["WEIGHT_LIMIT_TONS"] is not None else None,
            "weight_margin":     float(row["WEIGHT_MARGIN"]) if row["WEIGHT_MARGIN"] is not None else None,
            "clearance_margin":  float(row["CLEARANCE_MARGIN"]) if row["CLEARANCE_MARGIN"] is not None else None,
        }
        for row in veto_rows
    ]

    # ── Step 2: Aggregate across ALL intersecting bridges ─────────────────────
    agg_sql = _SQL_AGGREGATE.format(
        route_wkt=route_wkt.replace("'", "\\'"),
        vehicle_weight=vehicle_weight_tons,
        vehicle_height=vehicle_height_mt,
    )
    try:
        agg_rows = session.sql(agg_sql).collect()
    except Exception as exc:
        logger.error("[CPP Gate 3A] Aggregate query failed: %s", exc)
        raise

    agg = agg_rows[0] if agg_rows else None
    intersecting_count   = int(agg["INTERSECTING_COUNT"])   if agg and agg["INTERSECTING_COUNT"] is not None else 0
    min_weight_margin    = float(agg["MIN_WEIGHT_MARGIN"])  if agg and agg["MIN_WEIGHT_MARGIN"] is not None else None
    min_clearance_margin = float(agg["MIN_CLEARANCE_MARGIN"]) if agg and agg["MIN_CLEARANCE_MARGIN"] is not None else None

    # ── Step 3: Verdict ───────────────────────────────────────────────────────
    if not failing_bridges:
        logger.info(
            "[CPP Gate 3A] PASS — %d bridges intersect route, all within limits.",
            intersecting_count,
        )
        return ComplianceResult(
            verdict="PASS",
            failing_bridges=[],
            min_weight_margin=min_weight_margin,
            min_clearance_margin=min_clearance_margin,
            veto_reason="",
            intersecting_count=intersecting_count,
        )

    # Build veto reason
    weight_viols = [b for b in failing_bridges if b["weight_margin"] is not None and b["weight_margin"] < 1.0]
    height_viols = [b for b in failing_bridges if b["clearance_margin"] is not None and b["clearance_margin"] < 0.0]

    reasons = []
    if weight_viols:
        worst = min(weight_viols, key=lambda b: b["weight_margin"])
        reasons.append(
            f"weight limit exceeded on bridge {worst['bridge_id']} "
            f"(limit {worst['weight_limit_tons']:.1f} t < vehicle {vehicle_weight_tons:.1f} t)"
        )
    if height_viols:
        worst = min(height_viols, key=lambda b: b["clearance_margin"])
        reasons.append(
            f"height clearance insufficient on bridge {worst['bridge_id']} "
            f"(clearance {worst['clearance_mt']:.2f} m < vehicle {vehicle_height_mt:.2f} m)"
        )

    veto_reason = (
        f"HARD VETO — route blocked: {'; '.join(reasons)}. "
        f"({len(failing_bridges)} non-compliant bridge(s) of {intersecting_count} intersecting the route.)"
    )

    logger.warning("[CPP Gate 3A] %s", veto_reason)

    return ComplianceResult(
        verdict="HARD_VETO",
        failing_bridges=failing_bridges,
        min_weight_margin=min_weight_margin,
        min_clearance_margin=min_clearance_margin,
        veto_reason=veto_reason,
        intersecting_count=intersecting_count,
    )
