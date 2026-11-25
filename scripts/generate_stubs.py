"""Regenerate myml/__init__.pyi from packaged source templates."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "myml" / "templates"
ALIASES = {
    "LinearRegression": "linear_regression",
    "LogisticRegression": "logistic_regression",
    "tokenizer": "token",
}

lines = [
    '"""Generated declarations for myml verbatim templates and retrieval API."""',
    "from typing import Any, List, Optional, Union",
    "from .core import Snippet",
    "",
]
for path in sorted(TEMPLATES.glob("*.py")):
    if path.name.startswith("_"):
        continue
    lines.append(f"{path.stem}: Snippet")
for alias, canonical in sorted(ALIASES.items()):
    lines.append(f"{alias}: Snippet  # Alias for {canonical}")
lines += [
    "",
    "def get_template(name: str) -> Snippet: ...",
    "def template_names(include_aliases: bool = ...) -> List[str]: ...",
    "def list_templates() -> List[tuple]: ...",
    "def ask(query: str) -> Optional[Snippet]: ...",
    "def sug(query: Optional[str] = ..., rank: int = ...) -> Union[str, list]: ...",
    "def suggest(query: str = ..., limit: int = ...) -> List[str]: ...",
    "def reload_index() -> int: ...",
    "",
]
(ROOT / "myml" / "__init__.pyi").write_text(
    "\n".join(lines),
    encoding="utf-8",
    errors="replace",
)
print("Wrote myml/__init__.pyi")
