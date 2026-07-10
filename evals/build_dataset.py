"""Build the BeeDoula eval dataset in LangSmith.

Combines RAGAS-generated synthetic questions over the care-guideline corpus
with the hand-written golden questions from Task 1.

Run: uv run python build_dataset.py            (from evals/)
Env: EVAL_TESTSET_SIZE (default 8), EVAL_DATASET_NAME (default beedoula-eval-v1)
"""
from __future__ import annotations

import os
import sys
from pathlib import Path

import pandas as pd
from langchain_community.document_loaders import DirectoryLoader, PyMuPDFLoader, TextLoader
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langsmith import Client
from ragas.run_config import RunConfig
from ragas.testset import TestsetGenerator

from common import (
    DATASET_NAME,
    OUT_DIR,
    REPO_ROOT,
    build_generator_embeddings,
    build_generator_llm,
)
from golden import GOLDEN_EXAMPLES

TESTSET_SIZE = int(os.environ.get("EVAL_TESTSET_SIZE", "8"))


MAX_GENERATION_DOCS = int(os.environ.get("EVAL_MAX_GENERATION_DOCS", "20"))


def load_corpus():
    """RAGAS's transform pipeline (headline extraction -> splitting) fails on
    thin, image-heavy PDF pages. Merge pages per source, drop near-empty ones,
    and re-split into substantial sections so every node has enough text."""
    data_dir = str(REPO_ROOT / "data")
    raw = []
    for glob, loader_cls in (("**/*.pdf", PyMuPDFLoader), ("**/*.md", TextLoader)):
        raw.extend(DirectoryLoader(data_dir, glob=glob, loader_cls=loader_cls).load())

    by_source: dict[str, list[str]] = {}
    for doc in raw:
        text = doc.page_content.strip()
        if len(text) >= 200:
            by_source.setdefault(str(doc.metadata.get("source", "?")), []).append(text)

    splitter = RecursiveCharacterTextSplitter(chunk_size=6000, chunk_overlap=200)
    documents = []
    for source, pages in by_source.items():
        for i, section in enumerate(splitter.split_text("\n\n".join(pages))):
            documents.append(
                Document(page_content=section, metadata={"source": source, "section": i})
            )

    # Spread the cap across sources so one long PDF doesn't crowd out the rest.
    if len(documents) > MAX_GENERATION_DOCS:
        per_source: dict[str, list[Document]] = {}
        for doc in documents:
            per_source.setdefault(doc.metadata["source"], []).append(doc)
        picked, i = [], 0
        while len(picked) < MAX_GENERATION_DOCS:
            added = False
            for docs in per_source.values():
                if i < len(docs) and len(picked) < MAX_GENERATION_DOCS:
                    picked.append(docs[i])
                    added = True
            if not added:
                break
            i += 1
        documents = picked

    print(f"Loaded {len(raw)} pages -> {len(documents)} generation sections "
          f"from {len(by_source)} sources")
    return documents


def generate_synthetic(documents) -> pd.DataFrame:
    generator = TestsetGenerator(
        llm=build_generator_llm(),
        embedding_model=build_generator_embeddings(),
    )
    testset = generator.generate_with_langchain_docs(
        documents,
        testset_size=TESTSET_SIZE,
        run_config=RunConfig(max_workers=2, timeout=180),
        with_debugging_logs=False,
    )
    df = testset.to_pandas()
    print(f"Generated {len(df)} synthetic examples")
    return df


def as_string_list(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        return [str(v) for v in value]
    if hasattr(value, "tolist"):
        converted = value.tolist()
        if isinstance(converted, list):
            return [str(v) for v in converted]
    return [str(value)]


def main() -> None:
    client = Client()
    if client.has_dataset(dataset_name=DATASET_NAME):
        sys.exit(
            f"Dataset {DATASET_NAME!r} already exists in LangSmith. "
            "Set EVAL_DATASET_NAME to a new name, or delete the old dataset."
        )

    documents = load_corpus()
    synthetic_df = generate_synthetic(documents)

    examples = []
    for _, row in synthetic_df.iterrows():
        examples.append(
            {
                "inputs": {"question": str(row["user_input"])},
                "outputs": {
                    "answer": str(row["reference"]),
                    "reference_contexts": as_string_list(row.get("reference_contexts")),
                },
                "metadata": {
                    "source": "ragas-synthetic",
                    "kind": "corpus",
                    "synthesizer_name": str(row.get("synthesizer_name", "")),
                },
            }
        )
    for item in GOLDEN_EXAMPLES:
        examples.append(
            {
                "inputs": {"question": item["question"]},
                "outputs": {"answer": item["reference"], "reference_contexts": []},
                "metadata": {"source": "golden", "kind": item["kind"]},
            }
        )

    dataset = client.create_dataset(
        dataset_name=DATASET_NAME,
        description=(
            "BeeDoula infant-care eval set: RAGAS synthetic questions over the "
            "guideline corpus plus hand-written golden questions (corpus, "
            "memory, and web kinds)."
        ),
        metadata={"corpus": "data/", "testset_size": TESTSET_SIZE},
    )
    client.create_examples(dataset_id=dataset.id, examples=examples)
    print(f"Created LangSmith dataset {DATASET_NAME!r} with {len(examples)} examples "
          f"({len(synthetic_df)} synthetic + {len(GOLDEN_EXAMPLES)} golden)")

    backup = OUT_DIR / "dataset_backup.csv"
    pd.DataFrame(
        [
            {
                "question": e["inputs"]["question"],
                "reference": e["outputs"]["answer"],
                "source": e["metadata"]["source"],
                "kind": e["metadata"]["kind"],
            }
            for e in examples
        ]
    ).to_csv(backup, index=False)
    print(f"Backup written to {backup}")


if __name__ == "__main__":
    main()
