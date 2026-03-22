"""
cpp_agent.py — Compliance Pre-Processing (CPP) Pipeline Orchestrator
======================================================================
Orchestrates the CPP decision pipeline for the HyperLogistics SmartSC system.

Pipeline (in order):
  Gate 1 — compliance_agent: Spatial SQL hard veto (ST_INTERSECTS on bridges)
            → HARD VETO if any bridge on route is over-weight or under-clearance.
            → NO LLM is called if vetoed.
  Gate 2 — Snowflake Cortex LLM: Full CPP routing recommendation.
            → Only reached if Gate 1 PASS.

Usage:
    from src.agents.cpp_agent import run_cpp_pipeline, CPPDecision

    decision = run_cpp_pipeline(
        session=session,
        route_wkt="LINESTRING(-87.6298 41.8781, -90.1994 38.6270)",
        vehicle_weight_tons=40.0,
        vehicle_height_mt=4.5,
        user_query="Should I take I-55 from Chicago to St. Louis?",
    )
    print(decision.verdict)           # "PASS" or "HARD_VETO"
    print(decision.response_text)     # veto reason OR LLM answer
"""

import logging
from dataclasses import dataclass, field
from typing import Any

from src.agents.compliance_agent import ComplianceResult, check_route_compliance

logger = logging.getLogger(__name__)


# ─────────────────────────────────────────────────────────────────────────────
# Result dataclass
# ─────────────────────────────────────────────────────────────────────────────

@dataclass
class CPPDecision:
    """Full CPP pipeline output.

    Attributes:
        verdict:            "PASS" or "HARD_VETO"
        compliance:         The ComplianceResult from Gate 1.
        response_text:      Veto reason (if vetoed) or Cortex LLM answer (if passed).
        llm_called:         False if vetoed before LLM; True if LLM was invoked.
    """
    verdict: str
    compliance: ComplianceResult
    response_text: str = ""
    llm_called: bool = False


# ─────────────────────────────────────────────────────────────────────────────
# Cortex LLM helper (Gate 2 — only reached on PASS)
# ─────────────────────────────────────────────────────────────────────────────

_CORTEX_MODEL = "snowflake-arctic"

_SYSTEM_PROMPT_TEMPLATE = """
You are a logistics routing expert for HyperLogistics, a Smart Supply Chain
Optimization System. You have verified that the proposed route is structurally
compliant (weight and height limits satisfied for all {bridge_count} bridge(s)
intersected).

Minimum weight margin across route bridges: {min_weight_margin}
Minimum clearance margin across route bridges: {min_clearance_margin} m

User query: {user_query}

Provide a concise, professional routing recommendation based on the compliance
data above. Cite the margin figures in your response.
"""


def _call_cortex(session: Any, prompt: str) -> str:
    """Call Snowflake Cortex COMPLETE and return the text response."""
    clean_prompt = prompt.replace("'", "\\'")
    sql = f"SELECT SNOWFLAKE.CORTEX.COMPLETE('{_CORTEX_MODEL}', '{clean_prompt}')"
    try:
        rows = session.sql(sql).collect()
        return rows[0][0] if rows else "(no response from Cortex)"
    except Exception as exc:
        logger.error("[CPP Agent] Cortex call failed: %s", exc)
        return f"(Cortex error: {exc})"


# ─────────────────────────────────────────────────────────────────────────────
# Main pipeline entry point
# ─────────────────────────────────────────────────────────────────────────────

def run_cpp_pipeline(
    session: Any,
    route_wkt: str,
    vehicle_weight_tons: float,
    vehicle_height_mt: float,
    user_query: str = "",
) -> CPPDecision:
    """Run the full CPP pipeline for a proposed route.

    Gate 1 (compliance_agent) is ALWAYS executed first. If it issues a
    HARD_VETO the function returns immediately — the LLM is never called.
    Gate 2 (Cortex LLM) is only invoked when Gate 1 returns PASS.

    Args:
        session:              Active Snowflake Snowpark Session.
        route_wkt:            WKT LINESTRING for the proposed route.
        vehicle_weight_tons:  Gross vehicle weight in short tons.
        vehicle_height_mt:    Vehicle height in metres.
        user_query:           Optional natural-language question to pass to Cortex.

    Returns:
        CPPDecision with verdict, compliance result, and response text.
    """
    logger.info("[CPP Agent] Starting pipeline — route=%s…", route_wkt[:60])

    # ── GATE 1: Spatial SQL compliance hard veto ──────────────────────────────
    compliance = check_route_compliance(
        session=session,
        route_wkt=route_wkt,
        vehicle_weight_tons=vehicle_weight_tons,
        vehicle_height_mt=vehicle_height_mt,
    )

    if compliance.verdict == "HARD_VETO":
        logger.warning(
            "[CPP Agent] Gate 1 HARD VETO — pipeline halted. %s",
            compliance.veto_reason,
        )
        return CPPDecision(
            verdict="HARD_VETO",
            compliance=compliance,
            response_text=compliance.veto_reason,
            llm_called=False,
        )

    # ── GATE 2: Cortex LLM call (only on PASS) ───────────────────────────────
    logger.info(
        "[CPP Agent] Gate 1 PASS (%d bridges, min_weight_margin=%.3f, "
        "min_clearance_margin=%s m). Calling Cortex LLM.",
        compliance.intersecting_count,
        compliance.min_weight_margin if compliance.min_weight_margin is not None else 0.0,
        f"{compliance.min_clearance_margin:.2f}" if compliance.min_clearance_margin is not None else "N/A",
    )

    prompt = _SYSTEM_PROMPT_TEMPLATE.format(
        bridge_count=compliance.intersecting_count,
        min_weight_margin=(
            f"{compliance.min_weight_margin:.3f}"
            if compliance.min_weight_margin is not None
            else "N/A (no bridges on route)"
        ),
        min_clearance_margin=(
            f"{compliance.min_clearance_margin:.2f}"
            if compliance.min_clearance_margin is not None
            else "N/A (no bridges on route)"
        ),
        user_query=user_query or "Confirm route compliance status.",
    )

    llm_answer = _call_cortex(session, prompt)

    logger.info("[CPP Agent] Cortex response received (%d chars).", len(llm_answer))

    return CPPDecision(
        verdict="PASS",
        compliance=compliance,
        response_text=llm_answer,
        llm_called=True,
    )
