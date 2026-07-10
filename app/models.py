from __future__ import annotations

import os

from langchain_openai import ChatOpenAI

DEFAULT_CHAT_MODEL = "openai/gpt-5.4-mini"


def get_chat_model(model_name: str | None = None, *, temperature: float = 0) -> ChatOpenAI:
    """Chat model routed through an OpenAI-compatible LLM gateway.

    With LLM_GATEWAY_BASE_URL/LLM_GATEWAY_API_KEY set (Vercel AI Gateway),
    calls go through the gateway and model names are provider-prefixed
    (e.g. "openai/gpt-5.4-mini"). Unset, it falls back to OpenAI directly.
    """
    name = model_name or os.environ.get("OPENAI_CHAT_MODEL", DEFAULT_CHAT_MODEL)
    base_url = os.environ.get("LLM_GATEWAY_BASE_URL")
    api_key = (
        os.environ.get("LLM_GATEWAY_API_KEY") if base_url else None
    ) or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "No LLM credential: set LLM_GATEWAY_API_KEY + LLM_GATEWAY_BASE_URL "
            "(Vercel AI Gateway), or OPENAI_API_KEY for direct OpenAI."
        )
    if not base_url and "/" in name:
        name = name.split("/", 1)[1]
    return ChatOpenAI(
        model=name,
        temperature=temperature,
        api_key=api_key,
        base_url=base_url,
    )
