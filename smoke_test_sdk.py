"""Smoke-test the local agent server via the LangGraph SDK (README Part 1, step 4)."""

import asyncio

from langgraph_sdk import get_client


async def run(assistant_id: str, question: str) -> None:
    client = get_client(url="http://localhost:2024")
    print(f"\n=== {assistant_id}: {question} ===")
    async for chunk in client.runs.stream(
        None,
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


async def main() -> None:
    await run("simple_agent", "According to the cat health guidelines, what are the core vaccines for cats?")
    await run("agent_with_helpfulness", "How often should senior cats see the vet?")


asyncio.run(main())
