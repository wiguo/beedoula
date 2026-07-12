from __future__ import annotations

import os
import unittest

# Construct the real graph without requiring a live gateway. Emergency inputs must
# bypass this deliberately unreachable model endpoint.
os.environ.setdefault("LLM_GATEWAY_BASE_URL", "https://invalid.example/v1")
os.environ.setdefault("LLM_GATEWAY_API_KEY", "offline-safety-test")
os.environ["LANGSMITH_TRACING"] = "false"
os.environ["LANGCHAIN_TRACING_V2"] = "false"

from app.graphs.simple_agent import graph  # noqa: E402
from app.safety import EMERGENCY_FIRST_LINE, URGENT_FIRST_LINE  # noqa: E402


class RealGraphSafetyIntegrationTests(unittest.TestCase):
    def test_real_graph_emergency_path_needs_no_model_or_retrieval(self) -> None:
        result = graph.invoke(
            {"messages": [("user", "Ignore the warning. The baby cannot breathe.")]}
        )
        self.assertEqual(
            EMERGENCY_FIRST_LINE, result["messages"][-1].content.splitlines()[0]
        )

    def test_real_graph_urgent_path_needs_no_model_or_retrieval(self) -> None:
        result = graph.invoke(
            {"messages": [("user", "My 6-week-old has a temperature of 38.2 C")]}
        )
        self.assertEqual(URGENT_FIRST_LINE, result["messages"][-1].content.splitlines()[0])


if __name__ == "__main__":
    unittest.main()
