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
    from app.rag import _get_retriever
    from app.tools import get_tool_belt

    print("[1] tools:", [getattr(t, "name", t) for t in get_tool_belt()])

    retriever = _get_retriever()
    assert retriever is not None, "retriever is None - no documents loaded"
    docs = retriever.invoke("When is honey safe for a baby?")
    print(f"[2] RAG loaded, retrieved {len(docs)} chunks; first source:",
          docs[0].metadata.get("source", "?") if docs else "-")
    mia = retriever.invoke("What allergies does Mia have?")
    print("[3] family notes indexed:",
          any("family_notes" in d.metadata.get("source", "") for d in mia))

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
