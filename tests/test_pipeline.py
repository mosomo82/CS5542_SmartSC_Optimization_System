"""
tests/test_pipeline.py — Pipeline smoke tests
==============================================
Verifies that pipeline modules are importable and that the cpp_agent
orchestrator correctly gates the LLM call behind Gate 1.

Tests requiring live Snowflake credentials are skipped automatically
when SNOWFLAKE_ACCOUNT is absent from the environment.

Run:
    python -m pytest tests/test_pipeline.py -v
"""

import sys
import os
from unittest.mock import MagicMock
import pytest

# ── ensure project root is on sys.path ────────────────────────────────────────
PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, PROJECT_ROOT)

_HAS_SF_CREDS = all(
    os.getenv(k)
    for k in [
        "SNOWFLAKE_ACCOUNT",
        "SNOWFLAKE_USER",
        "SNOWFLAKE_DATABASE",
        "SNOWFLAKE_ROLE",
        "SNOWFLAKE_WAREHOUSE",
    ]
) and bool(os.getenv("SNOWFLAKE_PASSWORD") or os.getenv("SNOWFLAKE_PRIVATE_KEY_PATH"))

_skip_no_creds = pytest.mark.skipif(
    not _HAS_SF_CREDS,
    reason="Snowflake credentials not available in environment",
)


# ─────────────────────────────────────────────────────────────────────────────
# Mock helpers  (mirrors test_cpp_gate.py conventions)
# ─────────────────────────────────────────────────────────────────────────────

def _make_veto_row(bridge_id, clearance_mt, weight_limit_tons, vehicle_weight, vehicle_height):
    row = MagicMock()
    row.__getitem__ = lambda self, key: {
        "BRIDGE_ID":         bridge_id,
        "CLEARANCE_MT":      clearance_mt,
        "WEIGHT_LIMIT_TONS": weight_limit_tons,
        "WEIGHT_MARGIN":     weight_limit_tons / vehicle_weight,
        "CLEARANCE_MARGIN":  clearance_mt - vehicle_height,
    }[key]
    return row


def _make_agg_row(count, min_weight_margin, min_clearance_margin):
    row = MagicMock()
    row.__getitem__ = lambda self, key: {
        "INTERSECTING_COUNT":   count,
        "MIN_WEIGHT_MARGIN":    min_weight_margin,
        "MIN_CLEARANCE_MARGIN": min_clearance_margin,
    }[key]
    return row


# ─────────────────────────────────────────────────────────────────────────────
# Import tests
# ─────────────────────────────────────────────────────────────────────────────

class TestImports:

    def test_compliance_agent_importable(self):
        """compliance_agent exposes its public API without Snowflake creds."""
        from src.agents.compliance_agent import check_route_compliance, ComplianceResult
        assert callable(check_route_compliance)
        assert ComplianceResult is not None

    def test_cpp_agent_importable(self):
        """cpp_agent exposes its public API without Snowflake creds."""
        from src.agents.cpp_agent import run_cpp_pipeline, CPPDecision
        assert callable(run_cpp_pipeline)
        assert CPPDecision is not None

    @_skip_no_creds
    def test_snowflake_conn_importable(self):
        """snowflake_conn can be imported when credentials are present.

        snowflake_conn runs _assert_env() at import time, so this test is
        skipped in CI where Snowflake secrets are unavailable.
        """
        import src.utils.snowflake_conn as sf_conn
        assert callable(sf_conn.get_session)
        assert callable(sf_conn.close_session)
        assert callable(sf_conn.retry_snowflake)


# ─────────────────────────────────────────────────────────────────────────────
# CPP orchestrator tests
# ─────────────────────────────────────────────────────────────────────────────

class TestCPPOrchestrator:
    """Tests for cpp_agent.run_cpp_pipeline() — the Gate 1 → Gate 2 flow.

    test_cpp_gate.py covers compliance_agent in isolation; these tests cover
    the orchestrator logic: does a VETO really halt before the LLM? Does a
    PASS really invoke the LLM?
    """

    _ROUTE  = "LINESTRING(-87.6298 41.8781, -90.1994 38.6270)"
    _WEIGHT = 40.0   # tons
    _HEIGHT = 4.5    # metres

    def test_veto_halts_before_llm(self):
        """Gate 1 HARD_VETO must produce llm_called=False in the CPPDecision."""
        from src.agents.cpp_agent import run_cpp_pipeline

        veto_row = _make_veto_row("B_SMOKE_01", 3.5, 20.0, self._WEIGHT, self._HEIGHT)
        agg_row  = _make_agg_row(1, 20.0 / self._WEIGHT, 3.5 - self._HEIGHT)

        mock_sql_1 = MagicMock(); mock_sql_1.collect.return_value = [veto_row]
        mock_sql_2 = MagicMock(); mock_sql_2.collect.return_value = [agg_row]
        session = MagicMock()
        session.sql.side_effect = [mock_sql_1, mock_sql_2]

        decision = run_cpp_pipeline(
            session=session,
            route_wkt=self._ROUTE,
            vehicle_weight_tons=self._WEIGHT,
            vehicle_height_mt=self._HEIGHT,
            user_query="Can we take this route?",
        )

        assert decision.verdict == "HARD_VETO"
        assert decision.llm_called is False
        assert decision.response_text  # veto reason is populated
        # Cortex should never have been called — only 2 sql() calls expected
        assert session.sql.call_count == 2

    def test_pass_calls_llm(self):
        """Gate 1 PASS must invoke Cortex and produce llm_called=True."""
        from src.agents.cpp_agent import run_cpp_pipeline

        agg_row = _make_agg_row(3, 1.5, 0.8)

        mock_sql_1 = MagicMock(); mock_sql_1.collect.return_value = []          # no violations
        mock_sql_2 = MagicMock(); mock_sql_2.collect.return_value = [agg_row]   # aggregate
        mock_sql_3 = MagicMock(); mock_sql_3.collect.return_value = [["APPROVED: route is safe."]]  # Cortex

        session = MagicMock()
        session.sql.side_effect = [mock_sql_1, mock_sql_2, mock_sql_3]

        decision = run_cpp_pipeline(
            session=session,
            route_wkt=self._ROUTE,
            vehicle_weight_tons=self._WEIGHT,
            vehicle_height_mt=self._HEIGHT,
            user_query="Is this route compliant?",
        )

        assert decision.verdict == "PASS"
        assert decision.llm_called is True
        assert decision.response_text  # LLM answer is populated
        # All three sql() calls must have fired
        assert session.sql.call_count == 3
