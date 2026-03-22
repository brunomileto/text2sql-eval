from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from string import Formatter

_REPO_ROOT = Path(__file__).resolve().parents[3]
_PROMPTS_DIR = _REPO_ROOT / "config" / "prompts"


def _prompt_path(track_key: str) -> Path:
    key = track_key.strip().lower()
    if not key:
        raise ValueError("track_key cannot be empty")
    return _PROMPTS_DIR / f"{key}.txt"


def _required_fields(template: str) -> set[str]:
    formatter = Formatter()
    required: set[str] = set()
    for _, field_name, _, _ in formatter.parse(template):
        if not field_name:
            continue
        base_name = field_name.split(".", 1)[0].split("[", 1)[0]
        if base_name:
            required.add(base_name)
    return required


@lru_cache(maxsize=32)
def load_prompt_template(track_key: str) -> str:
    """Load prompt template text for a track key from config/prompts."""
    path = _prompt_path(track_key)
    if not path.exists():
        raise FileNotFoundError(f"Prompt template not found: {path}")
    return path.read_text(encoding="utf-8")


def render_prompt(track_key: str, context: dict[str, str]) -> str:
    """Render a prompt template with explicit context validation."""
    template = load_prompt_template(track_key)
    missing = sorted(_required_fields(template) - set(context))
    if missing:
        missing_list = ", ".join(missing)
        raise ValueError(
            f"Missing template variables for '{track_key}': {missing_list}"
        )
    return template.format(**context)
