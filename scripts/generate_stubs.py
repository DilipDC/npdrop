"""Generate explicit template attributes for Jedi/Pylance autocomplete."""
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
TEMPLATES=ROOT/"myml"/"templates"
out=['"""Generated template autocomplete declarations."""','from typing import Any','']
for path in sorted(TEMPLATES.glob("*.py")):
    if path.name.startswith("_"): continue
    name=path.stem
    desc=next((l.partition(":")[2].strip() for l in path.read_text().splitlines() if l.startswith("# Description:")),"Template source")
    out += [f"def {name}() -> Any: ...  # {desc}"]
(ROOT/"myml"/"__init__.pyi").write_text("\n".join(out)+"\n",encoding="utf-8")
print("Wrote myml/__init__.pyi")
