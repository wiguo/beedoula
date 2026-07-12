from __future__ import annotations

import json
import unittest
from pathlib import Path

from langchain_core.messages import AIMessage

from app.safety import (
    EMERGENCY_FIRST_LINE,
    URGENT_FIRST_LINE,
    build_safety_gated_graph,
    classify_safety,
    response_for_decision,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
DATASET_PATH = REPO_ROOT / "evals" / "safety_cases.jsonl"


def load_cases() -> list[dict]:
    return [
        json.loads(line)
        for line in DATASET_PATH.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


class SafetyDatasetTests(unittest.TestCase):
    def test_every_case_routes_as_expected(self) -> None:
        failures = []
        for case in load_cases():
            decision = classify_safety(case["messages"][-1])
            if decision.route != case["expected_route"]:
                failures.append(
                    f"{case['id']}: expected={case['expected_route']} "
                    f"actual={decision.route} rules={decision.matched_rule_ids}"
                )
        self.assertEqual([], failures, "\n".join(failures))

    def test_fixed_responses_start_with_required_instruction(self) -> None:
        for case in load_cases():
            decision = classify_safety(case["messages"][-1])
            response = response_for_decision(decision)
            if decision.route == "emergency":
                self.assertEqual(EMERGENCY_FIRST_LINE, response.splitlines()[0])
            elif decision.route == "urgent":
                self.assertEqual(URGENT_FIRST_LINE, response.splitlines()[0])
            else:
                self.assertEqual("", response)

    def test_adversarial_cases_cannot_override_routes(self) -> None:
        adversarial = [case for case in load_cases() if case.get("adversarial")]
        self.assertGreaterEqual(len(adversarial), 5)
        for case in adversarial:
            self.assertEqual(
                case["expected_route"], classify_safety(case["messages"][-1]).route
            )


class SafetyGraphTests(unittest.TestCase):
    def test_emergency_bypasses_agent(self) -> None:
        calls: list[str] = []

        def fake_agent(_state):
            calls.append("agent")
            return {"messages": [AIMessage(content="normal agent response")]}

        graph = build_safety_gated_graph(fake_agent)
        result = graph.invoke({"messages": [("user", "The baby cannot breathe")]})

        self.assertEqual([], calls)
        self.assertEqual(EMERGENCY_FIRST_LINE, result["messages"][-1].content.splitlines()[0])
        self.assertEqual(
            "emergency",
            result["messages"][-1].additional_kwargs["beedoula_safety"]["route"],
        )

    def test_urgent_bypasses_agent(self) -> None:
        calls: list[str] = []

        def fake_agent(_state):
            calls.append("agent")
            return {"messages": [AIMessage(content="normal agent response")]}

        graph = build_safety_gated_graph(fake_agent)
        result = graph.invoke(
            {"messages": [("user", "My 6-week-old has a temperature of 38.2 C")]}
        )

        self.assertEqual([], calls)
        self.assertEqual(URGENT_FIRST_LINE, result["messages"][-1].content.splitlines()[0])

    def test_routine_message_reaches_agent(self) -> None:
        calls: list[str] = []

        def fake_agent(_state):
            calls.append("agent")
            return {"messages": [AIMessage(content="normal agent response")]}

        graph = build_safety_gated_graph(fake_agent)
        result = graph.invoke({"messages": [("user", "What is Mia's nap schedule?")]})

        self.assertEqual(["agent"], calls)
        self.assertEqual("normal agent response", result["messages"][-1].content)


if __name__ == "__main__":
    unittest.main()
