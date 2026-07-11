from __future__ import annotations

import os
import re
from functools import lru_cache
from typing import Annotated

import tiktoken
from langchain_community.document_loaders import DirectoryLoader, PyMuPDFLoader, TextLoader
from langchain_core.tools import tool
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter
from rank_bm25 import BM25Okapi

DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"

# dense  - vector similarity only (baseline)
# hybrid - dense + BM25 fused with reciprocal rank fusion (Task 6 upgrade)
RETRIEVER_MODE = os.environ.get("RETRIEVER_MODE", "dense")
TOP_K = int(os.environ.get("RETRIEVER_TOP_K", "4"))
FIRST_STAGE_K = int(os.environ.get("RETRIEVER_FIRST_STAGE_K", "10"))


def _tiktoken_len(text: str) -> int:
    return len(tiktoken.encoding_for_model("gpt-4o").encode(text))


def _tokenize(text: str) -> list[str]:
    return re.findall(r"[a-z0-9]+", text.lower())


@lru_cache(maxsize=1)
def _get_index():
    """Load corpus once: chunks (for BM25) + Qdrant vector store (dense)."""
    data_dir = os.environ.get("RAG_DATA_DIR", "data")

    documents = []
    for glob, loader_cls in (("**/*.pdf", PyMuPDFLoader), ("**/*.md", TextLoader)):
        try:
            documents.extend(
                DirectoryLoader(data_dir, glob=glob, loader_cls=loader_cls).load()
            )
        except Exception:
            pass

    if not documents:
        return None

    splitter = RecursiveCharacterTextSplitter(
        chunk_size=750, chunk_overlap=0, length_function=_tiktoken_len
    )
    chunks = splitter.split_documents(documents)
    for i, chunk in enumerate(chunks):
        chunk.metadata["chunk_id"] = i

    base_url = os.environ.get("LLM_GATEWAY_BASE_URL")
    model = os.environ.get("OPENAI_EMBEDDING_MODEL", DEFAULT_EMBEDDING_MODEL)
    if base_url and "/" not in model:
        model = f"openai/{model}"
    elif not base_url and "/" in model:
        model = model.split("/", 1)[1]
    api_key = (
        os.environ.get("LLM_GATEWAY_API_KEY") if base_url else None
    ) or os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError(
            "No embeddings credential: set LLM_GATEWAY_API_KEY + "
            "LLM_GATEWAY_BASE_URL (Vercel AI Gateway), or OPENAI_API_KEY."
        )
    embeddings = OpenAIEmbeddings(
        model=model,
        api_key=api_key,
        base_url=base_url,
        check_embedding_ctx_length=not base_url,
    )
    vectorstore = QdrantVectorStore.from_documents(
        documents=chunks,
        embedding=embeddings,
        location=":memory:",
        collection_name="rag_collection",
    )
    bm25 = BM25Okapi([_tokenize(c.page_content) for c in chunks])
    return {"chunks": chunks, "vectorstore": vectorstore, "bm25": bm25}


def _dense_retrieve(index, query: str, k: int):
    return index["vectorstore"].similarity_search(query, k=k)


def _bm25_retrieve(index, query: str, k: int):
    scores = index["bm25"].get_scores(_tokenize(query))
    ranked = sorted(range(len(scores)), key=lambda i: scores[i], reverse=True)
    return [index["chunks"][i] for i in ranked[:k]]


def _reciprocal_rank_fusion(ranked_lists, *, limit: int, rrf_constant: int = 60):
    scores: dict[int, float] = {}
    docs_by_id: dict[int, object] = {}
    for ranked in ranked_lists:
        for rank, doc in enumerate(ranked, start=1):
            doc_id = doc.metadata["chunk_id"]
            docs_by_id.setdefault(doc_id, doc)
            scores[doc_id] = scores.get(doc_id, 0.0) + 1 / (rrf_constant + rank)
    top = sorted(scores.items(), key=lambda item: item[1], reverse=True)[:limit]
    return [docs_by_id[doc_id] for doc_id, _ in top]


@tool
def retrieve_information(
    query: Annotated[str, "query to ask the retrieve information tool"],
) -> str:
    """Retrieve infant-care information (babies 0-24 months) from vetted guidelines — feeding and nutrition (WHO), safe sleep (NICHD), developmental milestones (CDC), choking response and CPR (AHA) — and from this family's own care notes about their baby (allergies, routines, schedules, house rules)."""
    index = _get_index()
    if index is None:
        return "No relevant information found in the knowledge base."
    if RETRIEVER_MODE == "hybrid":
        docs = _reciprocal_rank_fusion(
            [
                _dense_retrieve(index, query, FIRST_STAGE_K),
                _bm25_retrieve(index, query, FIRST_STAGE_K),
            ],
            limit=TOP_K,
        )
    else:
        docs = _dense_retrieve(index, query, TOP_K)
    if not docs:
        return "No relevant information found in the knowledge base."
    return "\n\n".join(doc.page_content for doc in docs)
