"""Local smoke test: graph loads, RAG retrieves, memory tools work, agent answers.

Run: uv run python smoke_test_local.py
"""
from __future__ import annotations

from dotenv import load_dotenv

load_dotenv()


def main() -> None:
    from langgraph.checkpoint.memory import InMemorySaver
    from langgraph.store.memory import InMemoryStore

    from app.graphs.simple_agent import SYSTEM_PROMPT  # noqa: F401 - import check
    from app.models import get_chat_model
    from app.rag import retrieve_information
    from app.tools import get_tool_belt

    print("[1] tools:", [getattr(t, "name", t) for t in get_tool_belt()])

    honey_context = retrieve_information.invoke(
        {"query": "When is honey safe for a baby?"}
    )
    assert "honey" in honey_context.lower(), "RAG did not retrieve honey guidance"
    print(f"[2] RAG loaded, retrieved {len(honey_context)} characters")

    mia_context = retrieve_information.invoke(
        {"query": "What allergies does Mia have?"}
    )
    family_notes_found = "egg" in mia_context.lower() and "mia" in mia_context.lower()
    assert family_notes_found, "RAG did not retrieve Mia's family notes"
    print("[3] family notes indexed:", family_notes_found)

    print("[4] chat model:", get_chat_model().model_name)

    # Rebuild the agent with explicit checkpointer+store so memory tools work
    # outside the langgraph server (the server injects these in production).
    from langchain.agents import create_agent

    agent = create_agent(
        model=get_chat_model(),
        tools=get_tool_belt(),
        system_prompt=SYSTEM_PROMPT,
        checkpointer=InMemorySaver(),
        store=InMemoryStore(),
    )
    cfg = {"configurable": {"thread_id": "smoke-1"}}
    r1 = agent.invoke(
        {"messages": [("user", "Please remember: baby Mia is allergic to eggs.")]},
        cfg,
    )
    print("[5] memory write turn:", r1["messages"][-1].content[:160])

    r2 = agent.invoke(
        {"messages": [("user", "Can I give the baby scrambled eggs for lunch? She is 7 months.")]},
        {"configurable": {"thread_id": "smoke-2"}},  # new thread: long-term memory must carry over
    )
    answer = r2["messages"][-1].content
    print("[6] cross-thread answer:", answer[:300])
    assert "egg" in answer.lower(), "answer does not mention eggs"

    print("\nSMOKE TEST PASSED")


if __name__ == "__main__":
    main()
