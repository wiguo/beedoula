"""Run the BeeDoula eval harness: agent answers the LangSmith dataset, RAGAS
metrics judge the results, and a summary table lands in evals/out/.

Prereqs: agent server running (uv run langgraph dev --port 2024) and the
dataset built (build_dataset.py).

Run: uv run python run_evals.py            (from evals/)
Env: EVAL_EXPERIMENT_PREFIX (default "baseline"), EVAL_LIMIT (0 = all),
     BEEDOULA_API_URL (default http://localhost:2024)
"""
from __future__ import annotations

import asyncio
import os
from datetime import datetime, timezone

import pandas as pd
from langgraph_sdk import get_sync_client
from langsmith import Client, evaluate
from ragas.metrics.collections import AnswerAccuracy, ContextRecall, Faithfulness

from common import AGENT_URL, ASSISTANT_ID, DATASET_NAME, OUT_DIR, build_sync_judge_llm

EXPERIMENT_PREFIX = os.environ.get("EVAL_EXPERIMENT_PREFIX", "baseline")
EVAL_LIMIT = int(os.environ.get("EVAL_LIMIT", "0"))

PROFILE_NAMESPACE = ("beedoula", "baby_profile")
PROFILE_SEED = {
    "name": "The baby's name is Mia.",
    "date_of_birth": "Mia was born on 2025-12-02 (about 7 months old).",
    "allergies": "Mia is allergic to eggs (confirmed by allergist 2026-05-20). No egg in any form; check labels for albumin. Peanut introduced with no reaction.",
    "nap_schedule": "Two naps per day: 09:30-11:00 and 14:30-16:00.",
    "house_rules": "If fever is 38.0 C or higher, call the parents immediately. Any fall or head bump: call the parents right away, even if she seems fine.",
}

agent = get_sync_client(url=AGENT_URL)


def seed_profile() -> None:
    """Make memory-kind questions answerable: seed the store to match the
    family notes, overwriting anything smoke tests left behind."""
    for key, value in PROFILE_SEED.items():
        agent.store.put_item(PROFILE_NAMESPACE, key=key, value={"value": value})
    print(f"Seeded {len(PROFILE_SEED)} baby-profile facts at {AGENT_URL}")


def target(inputs: dict) -> dict:
    """One eval case: fresh thread, ask the question, capture the final answer
    and every tool result the agent retrieved along the way as contexts."""
    thread = agent.threads.create()
    result = agent.runs.wait(
        thread["thread_id"],
        ASSISTANT_ID,
        input={"messages": [{"role": "human", "content": inputs["question"]}]},
    )
    messages = result["messages"] if isinstance(result, dict) else result.values["messages"]
    contexts: list[str] = []
    answer = ""
    for msg in messages:
        msg_type = msg.get("type") if isinstance(msg, dict) else getattr(msg, "type", "")
        content = msg.get("content") if isinstance(msg, dict) else getattr(msg, "content", "")
        if not isinstance(content, str):
            content = str(content)
        if msg_type == "tool" and content.strip():
            contexts.append(content)
        elif msg_type == "ai" and content.strip():
            answer = content
    return {"answer": answer, "contexts": contexts}


judge = build_sync_judge_llm()
METRICS = {
    "context_recall": ContextRecall(llm=judge),
    "faithfulness": Faithfulness(llm=judge),
    "answer_accuracy": AnswerAccuracy(llm=judge),
}


def _score(metric_name: str, **kwargs) -> float | None:
    try:
        result = asyncio.run(METRICS[metric_name].ascore(**kwargs))
        return float(result.value)
    except Exception as exc:  # noqa: BLE001 - one failed judge call must not kill the run
        # ascii-safe: a cp1252 console must not crash the warning itself
        detail = repr(exc)[:200].encode("ascii", "replace").decode()
        print(f"  [warn] {metric_name} failed: {detail}")
        return None


def context_recall_evaluator(run, example) -> dict:
    return {
        "key": "context_recall",
        "score": _score(
            "context_recall",
            user_input=example.inputs["question"],
            retrieved_contexts=run.outputs.get("contexts") or [" "],
            reference=example.outputs["answer"],
        ),
    }


def faithfulness_evaluator(run, example) -> dict:
    return {
        "key": "faithfulness",
        "score": _score(
            "faithfulness",
            user_input=example.inputs["question"],
            response=run.outputs.get("answer") or " ",
            retrieved_contexts=run.outputs.get("contexts") or [" "],
        ),
    }


def answer_accuracy_evaluator(run, example) -> dict:
    return {
        "key": "answer_accuracy",
        "score": _score(
            "answer_accuracy",
            user_input=example.inputs["question"],
            response=run.outputs.get("answer") or " ",
            reference=example.outputs["answer"],
        ),
    }


def main() -> None:
    seed_profile()

    ls = Client()
    examples = list(ls.list_examples(dataset_name=DATASET_NAME))
    if EVAL_LIMIT:
        examples = examples[:EVAL_LIMIT]
    print(f"Evaluating {len(examples)} examples from {DATASET_NAME!r} "
          f"against {AGENT_URL} (prefix={EXPERIMENT_PREFIX!r})")

    results = evaluate(
        target,
        data=examples,
        evaluators=[
            context_recall_evaluator,
            faithfulness_evaluator,
            answer_accuracy_evaluator,
        ],
        experiment_prefix=EXPERIMENT_PREFIX,
        max_concurrency=2,
        metadata={"agent_url": AGENT_URL, "assistant_id": ASSISTANT_ID},
    )

    rows = []
    for item in results:
        example = item["example"]
        scores = {r.key: r.score for r in item["evaluation_results"]["results"]}
        rows.append(
            {
                "question": example.inputs["question"][:80],
                "kind": (example.metadata or {}).get("kind", "?"),
                "source": (example.metadata or {}).get("source", "?"),
                **scores,
            }
        )
    df = pd.DataFrame(rows)

    stamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    out_path = OUT_DIR / f"results_{EXPERIMENT_PREFIX}_{stamp}.csv"
    df.to_csv(out_path, index=False)

    metric_cols = [c for c in ("context_recall", "faithfulness", "answer_accuracy") if c in df]
    print("\n=== Mean scores overall ===")
    print(df[metric_cols].mean().round(3).to_string())
    print("\n=== Mean scores by kind ===")
    print(df.groupby("kind")[metric_cols].mean().round(3).to_string())
    print(f"\nPer-question results: {out_path}")
    print(f"Experiment name: {results.experiment_name}")


if __name__ == "__main__":
    main()
