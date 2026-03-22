"""
tests/test_cpp_gate.py — Unit tests for CPP Step 3A hard gate
==============================================================
Tests the compliance_agent.check_route_compliance() function using
a mocked Snowflake session. No live Snowflake connection is required.

Run:
    python -m pytest tests/test_cpp_gate.py -v
"""

import sys
import os
from unittest.mock import MagicMock, patch
import pytest

# ── ensure project root is on sys.path ────────────────────────────────────────
PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, PROJECT_ROOT)

from src.agents.compliance_agent import check_route_compliance, ComplianceResult


# ─────────────────────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────────────────────

_SAMPLE_ROUTE = "LINESTRING(-87.6298 41.8781, -90.1994 38.6270)"
_VEHICLE_WEIGHT = 40.0   # tons
_VEHICLE_HEIGHT = 4.5    # metres


def _make_veto_row(
    bridge_id: str,
    clearance_mt: float,
    weight_limit_tons: float,
    vehicle_weight: float,
    vehicle_height: float,
) -> MagicMock:
    """Factory: create a mock Snowpark Row for a violating bridge."""
    row = MagicMock()
    weight_margin    = weight_limit_tons / vehicle_weight
    clearance_margin = clearance_mt - vehicle_height
    row.__getitem__ = lambda self, key: {
        "BRIDGE_ID":          bridge_id,
        "CLEARANCE_MT":       clearance_mt,
        "WEIGHT_LIMIT_TONS":  weight_limit_tons,
        "WEIGHT_MARGIN":      weight_margin,
        "CLEARANCE_MARGIN":   clearance_margin,
    }[key]
    return row


def _make_agg_row(
    count: int,
    min_weight_margin: float,
    min_clearance_margin: float,
) -> MagicMock:
    """Factory: create a mock Snowpark Row for the aggregate query."""
    row = MagicMock()
    row.__getitem__ = lambda self, key: {
        "INTERSECTING_COUNT":   count,
        "MIN_WEIGHT_MARGIN":    min_weight_margin,
        "MIN_CLEARANCE_MARGIN": min_clearance_margin,
    }[key]
    return row


def _build_session(veto_rows, agg_count, agg_min_weight, agg_min_clearance):
    """Build a mock session whose .sql().collect() returns the given rows.

    First call  → veto_rows  (violating bridges query)
    Second call → [agg_row]  (aggregate query)
    """
    agg_row = _make_agg_row(agg_count, agg_min_weight, agg_min_clearance)

    mock_sql_result_1 = MagicMock()
    mock_sql_result_1.collect.return_value = veto_rows

    mock_sql_result_2 = MagicMock()
    mock_sql_result_2.collect.return_value = [agg_row]

    session = MagicMock()
    session.sql.side_effect = [mock_sql_result_1, mock_sql_result_2]
    return session


# ─────────────────────────────────────────────────────────────────────────────
# Tests
# ─────────────────────────────────────────────────────────────────────────────

class TestCPPGate:

    def test_overweight_veto(self):
        """Vehicle (40 t) exceeds bridge load limit (30 t) → HARD_VETO."""
        weight_limit = 30.0   # too light for the vehicle
        clearance    = 5.0    # height is fine

        veto_row = _make_veto_row(
            bridge_id="B001",
            clearance_mt=clearance,
            weight_limit_tons=weight_limit,
            vehicle_weight=_VEHICLE_WEIGHT,
            vehicle_height=_VEHICLE_HEIGHT,
        )
        session = _build_session(
            veto_rows=[veto_row],
            agg_count=3,
            agg_min_weight=weight_limit / _VEHICLE_WEIGHT,   # 0.75 < 1.0
            agg_min_clearance=clearance - _VEHICLE_HEIGHT,   # +0.5 m (OK)
        )

        result = check_route_compliance(
            session, _SAMPLE_ROUTE, _VEHICLE_WEIGHT, _VEHICLE_HEIGHT
        )

        assert result.verdict == "HARD_VETO", "Expected HARD_VETO for overweight vehicle"
        assert len(result.failing_bridges) == 1
        assert result.failing_bridges[0]["bridge_id"] == "B001"
        assert result.min_weight_margin < 1.0
        assert "weight" in result.veto_reason.lower()

    def test_height_veto(self):
        """Vehicle (4.5 m) exceeds bridge clearance (3.8 m) → HARD_VETO."""
        weight_limit = 50.0    # weight is fine
        clearance    = 3.8     # too low for the vehicle

        veto_row = _make_veto_row(
            bridge_id="B002",
            clearance_mt=clearance,
            weight_limit_tons=weight_limit,
            vehicle_weight=_VEHICLE_WEIGHT,
            vehicle_height=_VEHICLE_HEIGHT,
        )
        session = _build_session(
            veto_rows=[veto_row],
            agg_count=5,
            agg_min_weight=weight_limit / _VEHICLE_WEIGHT,    # 1.25 (OK)
            agg_min_clearance=clearance - _VEHICLE_HEIGHT,    # -0.7 m (violation)
        )

        result = check_route_compliance(
            session, _SAMPLE_ROUTE, _VEHICLE_WEIGHT, _VEHICLE_HEIGHT
        )

        assert result.verdict == "HARD_VETO", "Expected HARD_VETO for height violation"
        assert len(result.failing_bridges) == 1
        assert result.failing_bridges[0]["bridge_id"] == "B002"
        assert result.min_clearance_margin < 0.0
        assert "clearance" in result.veto_reason.lower()

    def test_compliant_pass(self):
        """All bridges within limits → PASS, no LLM blocked."""
        session = _build_session(
            veto_rows=[],           # no violating bridges returned
            agg_count=7,
            agg_min_weight=1.3,     # > 1.0 → safe
            agg_min_clearance=0.8,  # > 0.0 → safe
        )

        result = check_route_compliance(
            session, _SAMPLE_ROUTE, _VEHICLE_WEIGHT, _VEHICLE_HEIGHT
        )

        assert result.verdict == "PASS", "Expected PASS when all bridges are compliant"
        assert result.failing_bridges == []
        assert result.veto_reason == ""
        assert result.min_weight_margin is not None
        assert result.min_weight_margin >= 1.0
        assert result.intersecting_count == 7

    def test_no_bridges_on_route_pass(self):
        """No bridges intersect the route → PASS (open road)."""
        session = _build_session(
            veto_rows=[],   # no violating bridges
            agg_count=0,    # zero bridges on route at all
            agg_min_weight=None,
            agg_min_clearance=None,
        )
        # Aggregate row returns None for margins
        agg_row = MagicMock()
        agg_row.__getitem__ = lambda self, key: {
            "INTERSECTING_COUNT":   0,
            "MIN_WEIGHT_MARGIN":    None,
            "MIN_CLEARANCE_MARGIN": None,
        }[key]

        mock_sql_1 = MagicMock(); mock_sql_1.collect.return_value = []
        mock_sql_2 = MagicMock(); mock_sql_2.collect.return_value = [agg_row]
        session = MagicMock()
        session.sql.side_effect = [mock_sql_1, mock_sql_2]

        result = check_route_compliance(
            session, _SAMPLE_ROUTE, _VEHICLE_WEIGHT, _VEHICLE_HEIGHT
        )

        assert result.verdict == "PASS", "Expected PASS when no bridges on route"
        assert result.intersecting_count == 0
        assert result.min_weight_margin is None
        assert result.min_clearance_margin is None
        assert result.veto_reason == ""
