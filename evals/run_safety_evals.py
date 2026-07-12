"""Offline, deterministic evaluation of BeeDoula's pre-agent safety gate.

Run from the repository root:
    uv run python evals/run_safety_evals.py
"""

from __future__ import annotations

import csv
import json
import statistics
import sys
from datetime import datetime, timezone
from pathlib import Path
from time import perf_counter

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

from app.safety import (  # noqa: E402
    EMERGENCY_FIRST_LINE,
    URGENT_FIRST_LINE,
    classify_safety,
    percentile_95,
    response_for_decision,
)

DATASET_PATH = REPO_ROOT / "evals" / "safety_cases.jsonl"
OUT_DIR = REPO_ROOT / "evals" / "out"


def _ratio(numerator: int, denominator: int) -> float:
    return numerator / denominator if denominator else 0.0


def main() -> None:
    cases = [
        json.loads(line)
        for line in DATASET_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]
    rows = []
    latencies_ms = []

    for case in cases:
        started = perf_counter()
        decision = classify_safety(case["messages"][-1])
        latency_ms = (perf_counter() - started) * 1000
        latencies_ms.append(latency_ms)
        response = response_for_decision(decision)
        first_line = response.splitlines()[0] if response else ""
        required_first_line = {
            "emergency": EMERGENCY_FIRST_LINE,
            "urgent": URGENT_FIRST_LINE,
            "routine": "",
        }[case["expected_route"]]
        rows.append(
            {
                "id": case["id"],
                "category": case["category"],
                "adversarial": bool(case.get("adversarial")),
                "expected_route": case["expected_route"],
                "predicted_route": decision.route,
                "route_correct": decision.route == case["expected_route"],
                "first_line_correct": first_line == required_first_line,
                "matched_rule_ids": ";".join(decision.matched_rule_ids),
                "latency_ms": round(latency_ms, 4),
            }
        )

    emergency = [row for row in rows if row["expected_route"] == "emergency"]
    urgent = [row for row in rows if row["expected_route"] == "urgent"]
    routine = [row for row in rows if row["expected_route"] == "routine"]
    fixed_response_cases = emergency + urgent
    adversarial = [row for row in rows if row["adversarial"]]

    summary = {
        "dataset": str(DATASET_PATH.relative_to(REPO_ROOT)),
        "cases": len(rows),
        "emergency_cases": len(emergency),
        "urgent_cases": len(urgent),
        "routine_cases": len(routine),
        "fixed_response_cases": len(fixed_response_cases),
        "route_accuracy": _ratio(sum(row["route_correct"] for row in rows), len(rows)),
        "emergency_escalation_recall": _ratio(
            sum(row["predicted_route"] == "emergency" for row in emergency),
            len(emergency),
        ),
        "critical_miss_rate": _ratio(
            sum(row["predicted_route"] != "emergency" for row in emergency),
            len(emergency),
        ),
        "urgent_route_recall": _ratio(
            sum(row["predicted_route"] == "urgent" for row in urgent), len(urgent)
        ),
        "routine_over_escalation_rate": _ratio(
            sum(row["predicted_route"] != "routine" for row in routine), len(routine)
        ),
        "first_line_compliance": _ratio(
            sum(row["first_line_correct"] for row in fixed_response_cases),
            len(fixed_response_cases),
        ),
        "adversarial_route_accuracy": _ratio(
            sum(row["route_correct"] for row in adversarial), len(adversarial)
        ),
        "median_router_latency_ms": statistics.median(latencies_ms),
        "p95_router_latency_ms": percentile_95(latencies_ms),
    }

    OUT_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    csv_path = OUT_DIR / f"safety_results_{stamp}.csv"
    json_path = OUT_DIR / f"safety_summary_{stamp}.json"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    json_path.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")

    print(json.dumps(summary, indent=2))
    print(f"Per-case results: {csv_path}")
    print(f"Summary: {json_path}")

    failed = [row for row in rows if not row["route_correct"] or not row["first_line_correct"]]
    if failed:
        print("Failures:", file=sys.stderr)
        for row in failed:
            print(
                f"- {row['id']}: expected={row['expected_route']} "
                f"predicted={row['predicted_route']}",
                file=sys.stderr,
            )
        raise SystemExit(1)


if __name__ == "__main__":
    main()
