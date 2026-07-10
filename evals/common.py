"""Shared gateway clients and RAGAS plumbing for the BeeDoula eval harness.

Everything routes through the Vercel AI Gateway with the same vck_ key the
app uses (loaded from the repo-root .env). Patterns follow course sessions
5-6, which run this exact ragas build through the same gateway.
"""
from __future__ import annotations

import asyncio
import os
from pathlib import Path

import instructor
from dotenv import load_dotenv
from openai import OpenAI
from ragas.embeddings.base import embedding_factory
from ragas.llms import llm_factory

REPO_ROOT = Path(__file__).resolve().parents[1]
load_dotenv(REPO_ROOT / ".env")

GATEWAY_BASE_URL = os.environ.get("LLM_GATEWAY_BASE_URL", "https://ai-gateway.vercel.sh/v1")
GATEWAY_API_KEY = os.environ["LLM_GATEWAY_API_KEY"]
GENERATOR_MODEL = os.environ.get("OPENAI_CHAT_MODEL", "openai/gpt-5.4-mini")
JUDGE_MODEL = os.environ.get("EVAL_JUDGE_MODEL", GENERATOR_MODEL)
EMBEDDING_MODEL = os.environ.get("OPENAI_EMBEDDING_MODEL", "openai/text-embedding-3-small")

DATASET_NAME = os.environ.get("EVAL_DATASET_NAME", "beedoula-eval-v1")
AGENT_URL = os.environ.get("BEEDOULA_API_URL", "http://localhost:2024")
ASSISTANT_ID = "simple_agent"

OUT_DIR = Path(__file__).resolve().parent / "out"
OUT_DIR.mkdir(exist_ok=True)


def gateway_sync_client() -> OpenAI:
    client = OpenAI(api_key=GATEWAY_API_KEY, base_url=GATEWAY_BASE_URL)

    # Gateway/OpenAI embeddings reject empty strings with a 400; ragas graph
    # transforms occasionally emit one. Coerce to a single space.
    original_create = client.embeddings.create

    def _safe_embeddings_create(*args, **kwargs):
        value = kwargs.get("input")
        if isinstance(value, str) and not value.strip():
            kwargs["input"] = " "
        elif isinstance(value, list):
            kwargs["input"] = [
                v if not (isinstance(v, str) and not v.strip()) else " " for v in value
            ]
        return original_create(*args, **kwargs)

    client.embeddings.create = _safe_embeddings_create
    return client


def build_generator_llm():
    llm = llm_factory(
        GENERATOR_MODEL,
        provider="openai",
        client=gateway_sync_client(),
        mode=instructor.Mode.TOOLS,
        max_tokens=2048,
    )
    llm.model_args = {"max_tokens": 2048, "max_retries": 3}
    return llm


def build_generator_embeddings():
    return embedding_factory("openai", model=EMBEDDING_MODEL, client=gateway_sync_client())


def build_sync_judge_llm():
    """Judge with a sync gateway client, bridging ragas' async metric API.

    Instructor's AsyncOpenAI path is incompatible with nested event loops;
    keep gateway requests synchronous and bridge via asyncio.to_thread
    (same workaround as session 6).
    """
    judge = llm_factory(
        JUDGE_MODEL,
        provider="openai",
        client=gateway_sync_client(),
        mode=instructor.Mode.TOOLS,
        max_tokens=1024,
    )
    judge.model_args = {"max_tokens": 1024, "max_retries": 3}

    async def agenerate_from_sync(prompt, response_model):
        return await asyncio.to_thread(
            judge.generate, prompt=prompt, response_model=response_model
        )

    judge.agenerate = agenerate_from_sync
    return judge
