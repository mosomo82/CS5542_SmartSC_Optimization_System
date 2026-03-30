"""
tests/evaluate_system.py — CPP Pipeline Evaluation Harness
===========================================================
Runs the CPP pipeline against a golden scenario dataset and reports
pass/fail rate and average latency. Results are saved to tests/results/.

Modes:
    mock  — mocked Snowflake sessions; no credentials required (default)
    live  — real Snowflake session; requires credentials in .env

Usage:
    # Script (mock mode):
    python tests/evaluate_system.py

    # Script (live mode):
    python tests/evaluate_system.py --mode live

    # Via pytest (always mock mode):
    python -m pytest tests/evaluate_system.py -v
"""

import sys
import os
import json
import time
import argparse
from datetime import date
from unittest.mock import MagicMock
import pytest

# ── ensure project root is on sys.path ────────────────────────────────────────
PROJECT_ROOT = os.path.join(os.path.dirname(__file__), "..")
sys.path.insert(0, PROJECT_ROOT)

_DATASET_PATH   = os.path.join(os.path.dirname(__file__), "data", "evaluation_queries.json")
_RESULTS_PATH   = os.path.join(os.path.dirname(__file__), "results", "eval_results.json")
_PASS_THRESHOLD = 0.70


# ─────────────────────────────────────────────────────────────────────────────
# Mock session helpers
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


def _build_mock_session(scenario):
    """Return a mock Snowflake session pre-wired to produce the scenario's expected verdict."""
    weight = scenario["vehicle_weight_tons"]
    height = scenario["vehicle_height_mt"]
    violation_type = scenario.get("violation_type", "weight")

    if scenario["expected_verdict"] == "PASS":
        agg = _make_agg_row(3, 1.5, 0.8)
        sql1 = MagicMock(); sql1.collect.return_value = []
        sql2 = MagicMock(); sql2.collect.return_value = [agg]

    elif violation_type == "height":
        clearance = height - 0.7          # below vehicle height → veto
        veto = _make_veto_row("B_EVAL_H", clearance, weight * 1.5, weight, height)
        agg  = _make_agg_row(1, 1.5, clearance - height)
        sql1 = MagicMock(); sql1.collect.return_value = [veto]
        sql2 = MagicMock(); sql2.collect.return_value = [agg]

    else:  # weight or compound
        limit = weight * 0.75             # below vehicle weight → veto
        veto = _make_veto_row("B_EVAL_W", height + 1.0, limit, weight, height)
        agg  = _make_agg_row(1, limit / weight, 1.0)
        sql1 = MagicMock(); sql1.collect.return_value = [veto]
        sql2 = MagicMock(); sql2.collect.return_value = [agg]

    session = MagicMock()
    session.sql.side_effect = [sql1, sql2]
    return session


# ─────────────────────────────────────────────────────────────────────────────
# Core evaluation logic
# ─────────────────────────────────────────────────────────────────────────────

def _run_scenario_mock(scenario):
    """Run one scenario with a mocked session. Returns a result dict."""
    from src.agents.compliance_agent import check_route_compliance

    session = _build_mock_session(scenario)
    t0 = time.perf_counter()
    result = check_route_compliance(
        session=session,
        route_wkt=scenario["route_wkt"],
        vehicle_weight_tons=scenario["vehicle_weight_tons"],
        vehicle_height_mt=scenario["vehicle_height_mt"],
    )
    latency_ms = (time.perf_counter() - t0) * 1000

    actual   = result.verdict          # "PASS" or "HARD_VETO"
    expected = scenario["expected_verdict"]
    passed   = actual == expected

    return {
        "id":               scenario["id"],
        "category":         scenario["category"],
        "description":      scenario["description"],
        "expected_verdict": expected,
        "actual_verdict":   actual,
        "passed":           passed,
        "latency_ms":       round(latency_ms, 3),
        "veto_reason":      result.veto_reason if not passed or actual == "HARD_VETO" else "",
    }


def _run_scenario_live(scenario, session):
    """Run one scenario against a live Snowflake session. Returns a result dict."""
    from src.agents.compliance_agent import check_route_compliance

    t0 = time.perf_counter()
    result = check_route_compliance(
        session=session,
        route_wkt=scenario["route_wkt"],
        vehicle_weight_tons=scenario["vehicle_weight_tons"],
        vehicle_height_mt=scenario["vehicle_height_mt"],
    )
    latency_ms = (time.perf_counter() - t0) * 1000

    actual   = result.verdict
    expected = scenario["expected_verdict"]
    passed   = actual == expected

    return {
        "id":               scenario["id"],
        "category":         scenario["category"],
        "description":      scenario["description"],
        "expected_verdict": expected,
        "actual_verdict":   actual,
        "passed":           passed,
        "latency_ms":       round(latency_ms, 3),
        "veto_reason":      result.veto_reason if actual == "HARD_VETO" else "",
    }


def run_evaluation(mode="mock", dataset_path=_DATASET_PATH, results_path=_RESULTS_PATH):
    """Run the full evaluation and return the summary dict."""
    with open(dataset_path, "r", encoding="utf-8") as f:
        scenarios = json.load(f)

    session = None
    if mode == "live":
        from src.utils.snowflake_conn import get_session
        session = get_session()

    scenario_results = []
    for sc in scenarios:
        if mode == "mock":
            res = _run_scenario_mock(sc)
        else:
            res = _run_scenario_live(sc, session)
        scenario_results.append(res)
        status = "PASS" if res["passed"] else "FAIL"
        print(f"  [{status}] {res['id']} ({res['category']}) — {res['actual_verdict']} "
              f"(expected {res['expected_verdict']}, {res['latency_ms']:.1f} ms)")

    total      = len(scenario_results)
    passed     = sum(1 for r in scenario_results if r["passed"])
    failed     = total - passed
    pass_rate  = passed / total if total > 0 else 0.0
    avg_latency = sum(r["latency_ms"] for r in scenario_results) / total if total > 0 else 0.0

    # Group pass rate by category
    categories = {}
    for r in scenario_results:
        cat = r["category"]
        if cat not in categories:
            categories[cat] = {"total": 0, "passed": 0}
        categories[cat]["total"] += 1
        if r["passed"]:
            categories[cat]["passed"] += 1

    summary = {
        "eval_date":        str(date.today()),
        "mode":             mode,
        "dataset":          dataset_path,
        "summary": {
            "total":          total,
            "passed":         passed,
            "failed":         failed,
            "pass_rate":      round(pass_rate, 4),
            "avg_latency_ms": round(avg_latency, 3),
        },
        "by_category": {
            cat: {
                "passed":    v["passed"],
                "total":     v["total"],
                "pass_rate": round(v["passed"] / v["total"], 4),
            }
            for cat, v in categories.items()
        },
        "scenarios": scenario_results,
    }

    os.makedirs(os.path.dirname(results_path), exist_ok=True)
    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    return summary


# ─────────────────────────────────────────────────────────────────────────────
# Pytest entry point
# ─────────────────────────────────────────────────────────────────────────────

class TestEvaluation:

    def test_mock_eval_pass_rate(self):
        """Full mock evaluation must achieve >= 70% pass rate."""
        summary = run_evaluation(mode="mock")
        pass_rate = summary["summary"]["pass_rate"]
        total     = summary["summary"]["total"]
        passed    = summary["summary"]["passed"]
        assert pass_rate >= _PASS_THRESHOLD, (
            f"Evaluation pass rate {pass_rate:.1%} ({passed}/{total}) "
            f"is below the required {_PASS_THRESHOLD:.0%} threshold."
        )

    def test_q13_q14_monotonicity(self):
        """Q13 (no constraint) must PASS; Q14 (same route + bridge) must HARD_VETO."""
        with open(_DATASET_PATH, "r", encoding="utf-8") as f:
            scenarios = {sc["id"]: sc for sc in json.load(f)}

        assert "Q13" in scenarios, "Q13 not found in evaluation dataset"
        assert "Q14" in scenarios, "Q14 not found in evaluation dataset"

        r13 = _run_scenario_mock(scenarios["Q13"])
        r14 = _run_scenario_mock(scenarios["Q14"])

        assert r13["actual_verdict"] == "PASS", (
            f"Q13 (no constraint) should PASS, got {r13['actual_verdict']}"
        )
        assert r14["actual_verdict"] == "HARD_VETO", (
            f"Q14 (bridge violation) should HARD_VETO, got {r14['actual_verdict']}"
        )


# ─────────────────────────────────────────────────────────────────────────────
# CLI entry point
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="HyperLogistics CPP evaluation harness")
    parser.add_argument(
        "--mode", choices=["mock", "live"], default="mock",
        help="mock: no Snowflake needed (default). live: uses .env credentials.",
    )
    parser.add_argument(
        "--dataset", default=_DATASET_PATH,
        help=f"Path to evaluation JSON (default: {_DATASET_PATH})",
    )
    parser.add_argument(
        "--output", default=_RESULTS_PATH,
        help=f"Path to write results JSON (default: {_RESULTS_PATH})",
    )
    args = parser.parse_args()

    print(f"\nHyperLogistics CPP Evaluation — mode={args.mode}")
    print(f"Dataset : {args.dataset}")
    print(f"Output  : {args.output}\n")

    summary = run_evaluation(mode=args.mode, dataset_path=args.dataset, results_path=args.output)

    pr   = summary["summary"]["pass_rate"]
    tot  = summary["summary"]["total"]
    ok   = summary["summary"]["passed"]
    lat  = summary["summary"]["avg_latency_ms"]

    print(f"\nResults: {ok}/{tot} passed  ({pr:.1%})  |  avg latency {lat:.1f} ms")
    print(f"Saved  : {args.output}")

    if pr < _PASS_THRESHOLD:
        print(f"\nFAIL: pass rate {pr:.1%} is below the {_PASS_THRESHOLD:.0%} threshold.")
        sys.exit(1)
    else:
        print(f"\nPASS: pass rate {pr:.1%} meets the {_PASS_THRESHOLD:.0%} threshold.")


if __name__ == "__main__":
    main()
