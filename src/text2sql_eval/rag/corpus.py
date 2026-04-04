from __future__ import annotations

from pathlib import Path

from .models import CorpusDocument

_REPO_ROOT = Path(__file__).resolve().parents[3]
DEFAULT_CORPUS_DIR = _REPO_ROOT / "docs" / "rag"
SUPPORTED_SUFFIXES = {".md", ".txt"}


def load_corpus_documents(
    corpus_dir: Path = DEFAULT_CORPUS_DIR,
) -> list[CorpusDocument]:
    if not corpus_dir.exists():
        raise FileNotFoundError(f"RAG corpus directory not found: {corpus_dir}")

    documents: list[CorpusDocument] = []
    for path in sorted(corpus_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in SUPPORTED_SUFFIXES:
            continue
        content = path.read_text(encoding="utf-8").strip()
        if not content:
            continue
        documents.append(
            CorpusDocument(
                source_path=str(path.relative_to(corpus_dir.parent.parent)),
                content=content,
            )
        )

    if not documents:
        raise ValueError(f"No RAG corpus documents found in {corpus_dir}")

    return documents
