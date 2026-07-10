from __future__ import annotations

import os
from functools import lru_cache
from typing import Annotated

import tiktoken
from langchain_community.document_loaders import DirectoryLoader, PyMuPDFLoader, TextLoader
from langchain_core.tools import tool
from langchain_openai.embeddings import OpenAIEmbeddings
from langchain_qdrant import QdrantVectorStore
from langchain_text_splitters import RecursiveCharacterTextSplitter

DEFAULT_EMBEDDING_MODEL = "text-embedding-3-small"


def _tiktoken_len(text: str) -> int:
    return len(tiktoken.encoding_for_model("gpt-4o").encode(text))


@lru_cache(maxsize=1)
def _get_retriever():
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

    # Embeddings follow the same gateway routing as chat (see app/models.py).
    # Gateways expect plain-string input, hence check_embedding_ctx_length=False.
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
    return vectorstore.as_retriever()


@tool
def retrieve_information(
    query: Annotated[str, "query to ask the retrieve information tool"],
) -> str:
    """Retrieve infant-care information (babies 0-24 months) from vetted guidelines — feeding and nutrition (WHO), safe sleep (NICHD), developmental milestones (CDC), choking response and CPR (AHA) — and from this family's own care notes about their baby (allergies, routines, schedules, house rules)."""
    retriever = _get_retriever()
    docs = retriever.invoke(query) if retriever else []
    if not docs:
        return "No relevant information found in the knowledge base."
    return "\n\n".join(doc.page_content for doc in docs)
