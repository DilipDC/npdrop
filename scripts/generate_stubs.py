"""Generate explicit template and alias declarations for IDE completion."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEMPLATES = ROOT / "myml" / "templates"
ALIASES = {
    "LinearRegression": "linear_regression",
    "LogisticRegression": "logistic_regression",
    "tokenizer": "token",
}

lines = [
    '"""Generated template attribute declarations for editor completion."""',
    "from typing import Any, List, Optional",
    "from .core import Snippet",
    "",
]
for path in sorted(TEMPLATES.glob("*.py")):
    if path.name.startswith("_"):
        continue
    name = path.stem
    first = path.read_text(encoding="utf-8").splitlines()[:1]
    desc = first[0].partition(":")[2].strip() if first and first[0].startswith("# Description:") else "Source code template"
    lines.append(f"{name}: Snippet  # {desc}")
for alias, canonical in sorted(ALIASES.items()):
    lines.append(f"{alias}: Snippet  # Alias for {canonical}")
lines += [
    "",
    "def suggest(prefix: str = '', previous_line: Optional[str] = None, limit: int = 15) -> List[str]: ...",
    "def reload_index() -> Any: ...",
    "",
]
(ROOT / "myml" / "__init__.pyi").write_text("\n".join(lines), encoding="utf-8")
print("Wrote myml/__init__.pyi")
