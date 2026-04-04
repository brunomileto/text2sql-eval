from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class RagConfig:
    backend: str
    top_k: int
    embedding_model: str
    index_path: str


@dataclass(frozen=True)
class CorpusDocument:
    source_path: str
    content: str


@dataclass(frozen=True)
class RagChunk:
    chunk_id: str
    source_path: str
    text: str
    chunk_index: int


@dataclass(frozen=True)
class RetrievedChunk:
    chunk_id: str
    source_path: str
    text: str
    score: float
    chunk_index: int


@dataclass(frozen=True)
class RagIndexBuildResult:
    index_path: str
    manifest_path: str
    source_count: int
    chunk_count: int
