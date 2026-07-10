"""Smoke-test the local agent server via the LangGraph SDK.

Start the server first: uv run langgraph dev --port 2024
"""

import asyncio

from langgraph_sdk import get_client


async def run(assistant_id: str, question: str, thread_id: str | None = None) -> str | None:
    client = get_client(url="http://localhost:2024")
    print(f"\n=== {assistant_id}: {question} ===")
    if thread_id is None:
        thread = await client.threads.create()
        thread_id = thread["thread_id"]
    async for chunk in client.runs.stream(
        thread_id,
        assistant_id,
        input={"messages": [{"role": "human", "content": question}]},
        stream_mode="updates",
    ):
        if chunk.event != "updates" or not isinstance(chunk.data, dict):
            continue
        for node, update in chunk.data.items():
            for msg in (update or {}).get("messages", []):
                content = msg.get("content") or ""
                calls = [tc["name"] for tc in msg.get("tool_calls", [])]
                if calls:
                    print(f"[{node}] tool calls: {calls}")
                elif content:
                    text = content if isinstance(content, str) else str(content)
                    print(f"[{node}] {text[:300]}")
    return thread_id


async def main() -> None:
    # RAG grounding
    await run("simple_agent", "Is honey safe for a 10-month-old?")
    # Memory write, then cross-thread recall (server-provided store)
    await run("simple_agent", "Please remember that baby Mia moved to one nap, 12:30 to 14:30.")
    await run("simple_agent", "What is the baby's nap schedule?")


asyncio.run(main())
