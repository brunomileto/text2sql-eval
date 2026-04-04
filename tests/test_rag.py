from __future__ import annotations

import json

import pytest

from text2sql_eval.config import (
    AppConfig,
    InputsConfig,
    LLMModelConfig,
    RunDefaultsConfig,
)
from text2sql_eval.rag.builder import build_rag_index
from text2sql_eval.rag.chunking import chunk_documents
from text2sql_eval.rag.config import parse_rag_config
from text2sql_eval.rag.corpus import load_corpus_documents
from text2sql_eval.rag.models import CorpusDocument, RagIndexBuildResult
from text2sql_eval.rag.retriever import build_retriever


def _base_config(tmp_path) -> AppConfig:
    return AppConfig(
        models=[
            LLMModelConfig(
                provider="fake",
                model="local-test",
                temperature=0.0,
                max_tokens=32,
            )
        ],
        inputs=InputsConfig(
            questions_file="data/dev.json",
            database_file="data/database.sqlite",
        ),
        run_defaults=RunDefaultsConfig(tracks=["a"], limit=None, output_dir="results/"),
        rag={
            "backend": "chroma",
            "top_k": 5,
            "embedding_model": "text-embedding-3-small",
            "index_path": str(tmp_path / "rag-index"),
        },
    )


def test_parse_rag_config_validates_required_fields(tmp_path):
    config = parse_rag_config(_base_config(tmp_path).rag)

    assert config.backend == "chroma"
    assert config.top_k == 5


@pytest.mark.parametrize(
    ("rag_config", "message"),
    [
        ({}, "Missing required 'rag' configuration"),
        (
            {"backend": "faiss", "top_k": 5, "embedding_model": "m", "index_path": "i"},
            "Unsupported RAG backend",
        ),
        (
            {
                "backend": "chroma",
                "top_k": 0,
                "embedding_model": "m",
                "index_path": "i",
            },
            "'rag.top_k' must be >= 1",
        ),
    ],
)
def test_parse_rag_config_rejects_invalid_config(rag_config, message):
    with pytest.raises(ValueError, match=message):
        parse_rag_config(rag_config)


def test_load_corpus_documents_reads_supported_files(tmp_path):
    corpus_dir = tmp_path / "docs" / "rag"
    corpus_dir.mkdir(parents=True)
    (corpus_dir / "a.md").write_text("# A", encoding="utf-8")
    (corpus_dir / "b.txt").write_text("hello", encoding="utf-8")
    (corpus_dir / "skip.json").write_text("{}", encoding="utf-8")

    documents = load_corpus_documents(corpus_dir)

    assert [document.source_path for document in documents] == [
        "docs/rag/a.md",
        "docs/rag/b.txt",
    ]


def test_chunk_documents_splits_large_document():
    documents = [
        CorpusDocument(source_path="docs/rag/a.md", content="x" * 2000),
    ]

    chunks = chunk_documents(documents)

    assert len(chunks) >= 2
    assert chunks[0].source_path == "docs/rag/a.md"
    assert chunks[0].chunk_index == 0


def test_build_rag_index_writes_manifest_and_uses_vector_store(monkeypatch, tmp_path):
    corpus_dir = tmp_path / "docs" / "rag"
    corpus_dir.mkdir(parents=True)
    (corpus_dir / "a.md").write_text("alpha\nbeta", encoding="utf-8")

    captured: dict[str, object] = {}

    class FakeVectorStore:
        @classmethod
        def from_env(cls, *, index_path, embedding_model):
            captured["index_path"] = str(index_path)
            captured["embedding_model"] = embedding_model
            return cls()

        def reset(self) -> None:
            captured["reset"] = True

        def upsert(self, chunks) -> None:
            captured["chunks"] = chunks

    from text2sql_eval.rag import builder

    monkeypatch.setattr(builder, "ChromaVectorStore", FakeVectorStore)

    result = build_rag_index(_base_config(tmp_path), corpus_dir=corpus_dir)

    manifest_path = tmp_path / "rag-index" / "manifest.json"
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))

    assert isinstance(result, RagIndexBuildResult)
    assert result.source_count == 1
    assert result.chunk_count == len(captured["chunks"])
    assert captured["reset"] is True
    assert manifest["source_count"] == 1
    assert manifest["sources"][0]["source_path"] == "docs/rag/a.md"
    assert "char_count" in manifest["sources"][0]


def test_build_retriever_requires_manifest(tmp_path):
    with pytest.raises(FileNotFoundError, match="build-rag-index"):
        build_retriever(_base_config(tmp_path))
