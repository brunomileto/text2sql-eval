from __future__ import annotations

import hashlib

from .models import CorpusDocument, RagChunk

MAX_CHUNK_CHARS = 1200
CHUNK_OVERLAP_CHARS = 200


def chunk_documents(documents: list[CorpusDocument]) -> list[RagChunk]:
    chunks: list[RagChunk] = []
    for document in documents:
        for chunk_index, text in enumerate(_chunk_text(document.content)):
            digest = hashlib.sha256(
                f"{document.source_path}:{chunk_index}:{text}".encode()
            ).hexdigest()[:12]
            chunks.append(
                RagChunk(
                    chunk_id=f"{document.source_path}:{chunk_index}:{digest}",
                    source_path=document.source_path,
                    text=text,
                    chunk_index=chunk_index,
                )
            )
    return chunks


def _chunk_text(text: str) -> list[str]:
    cleaned = text.strip()
    if not cleaned:
        return []
    if len(cleaned) <= MAX_CHUNK_CHARS:
        return [cleaned]

    chunks: list[str] = []
    start = 0
    step = MAX_CHUNK_CHARS - CHUNK_OVERLAP_CHARS
    while start < len(cleaned):
        chunk = cleaned[start : start + MAX_CHUNK_CHARS].strip()
        if chunk:
            chunks.append(chunk)
        start += step
    return chunks
