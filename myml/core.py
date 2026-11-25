"""Template discovery, safe source delivery, and fuzzy template search."""
from __future__ import annotations

import difflib
import html
import re
import sys
from importlib import resources
from pathlib import Path

ALIASES = {
    "LinearRegression": "linear_regression",
    "LogisticRegression": "logistic_regression",
    "tokenizer": "token",
}


def _template_files():
    """Return packaged Python source resources without importing them."""
    root = resources.files(__package__).joinpath("templates")
    return {
        item.name[:-3]: item
        for item in root.iterdir()
        if item.name.endswith(".py") and not item.name.startswith("_")
    }


def template_names(include_aliases: bool = False):
    names = sorted(_template_files())
    if include_aliases:
        names.extend(sorted(ALIASES))
    return names


def resolve_template_name(name: str) -> str:
    canonical = ALIASES.get(name, name)
    if canonical not in _template_files():
        raise KeyError(name)
    return canonical


def _read(name: str) -> str:
    canonical = resolve_template_name(name)
    return _template_files()[canonical].read_text(encoding="utf-8")


def _description(code: str) -> str:
    first = code.splitlines()[0].strip() if code.splitlines() else ""
    if first.startswith("# Description:"):
        return first.partition(":")[2].strip()
    for line in code.splitlines()[:8]:
        if line.lstrip().startswith(('"""', "'''")):
            return line.strip("\"' ")[:180]
    return "Python code template"


def _clean_for_insert(code: str) -> str:
    lines = code.splitlines(keepends=True)
    if lines and lines[0].lstrip().startswith("# Description:"):
        return "".join(lines[1:])
    return code


class Snippet:
    """A source snippet; access .code to retrieve text without execution."""

    def __init__(self, name: str, code: str):
        self.name = resolve_template_name(name)
        self.code = code
        self.description = _description(code)

    def show(self):
        _deliver(self.name, self.code)
        return self

    def insert(self, replace: bool = False):
        code = _clean_for_insert(self.code)
        try:
            from IPython import get_ipython
            shell = get_ipython()
            manager = getattr(shell, "payload_manager", None) if shell else None
            if manager is not None:
                manager.write_payload(
                    {"source": "set_next_input", "text": code, "replace": replace},
                    single=False,
                )
                return self
        except Exception:
            pass
        print(code)
        return self

    def save(self, filename):
        path = Path(filename)
        path.write_text(self.code, encoding="utf-8")
        return path

    def __repr__(self):
        return f"Snippet({self.name!r}: {self.description})"


def get_template(name: str) -> Snippet:
    canonical = resolve_template_name(name)
    return Snippet(canonical, _read(canonical))


def _colab_copy_card(name: str, code: str) -> bool:
    try:
        from IPython.display import HTML, display

        escaped = html.escape(code)
        safe_name = html.escape(name)
        card = f"""<div style="border:1px solid #d0d7de;border-radius:12px;padding:14px;margin:8px 0;font-family:system-ui">
<h3 style="margin:0 0 8px">myml · {safe_name}</h3>
<button style="padding:7px 12px;border:0;border-radius:7px;background:#1463d5;color:#fff;cursor:pointer" onclick="navigator.clipboard.writeText(this.nextElementSibling.innerText).then(()=>this.innerText='Copied!')">Copy code</button>
<pre style="white-space:pre-wrap;overflow:auto;max-height:520px;background:#f6f8fa;padding:12px;border-radius:7px"><code>{escaped}</code></pre></div>"""
        display(HTML(card))
        return True
    except Exception:
        return False


def _deliver(name: str, code: str) -> None:
    """Insert into the next Jupyter cell, or create a Colab scratch cell."""
    clean_code = _clean_for_insert(code)

    # Colab must be handled before generic IPython payload delivery.
    try:
        from google.colab import _frontend  # type: ignore
        _frontend.create_scratch_cell(clean_code)
        return
    except Exception:
        # Colab scratch-cell API is not available in every Colab release.
        if "google.colab" in sys.modules:
            if _colab_copy_card(name, clean_code):
                return
            print(clean_code)
            return

    # Local Jupyter/JupyterLab/Notebook: queue a distinct next-input payload.
    try:
        from IPython import get_ipython
        shell = get_ipython()
        manager = getattr(shell, "payload_manager", None) if shell else None
        if manager is not None:
            manager.write_payload(
                {"source": "set_next_input", "text": clean_code, "replace": False},
                single=False,
            )
            return
    except Exception:
        # Never show a Colab HTML card in a local notebook on failure.
        pass

    # Non-notebook Python sessions have no editable cell to target.
    print(clean_code)


def list_templates():
    rows = [(name, _description(_read(name))) for name in template_names()]
    try:
        from IPython.display import HTML, display
        body = "".join(
            f"<tr><td><code>{html.escape(name)}</code></td><td>{html.escape(desc)}</td></tr>"
            for name, desc in rows
        )
        display(HTML("<table><thead><tr><th>Template</th><th>Description</th></tr></thead><tbody>" + body + "</tbody></table>"))
    except Exception:
        for name, desc in rows:
            print(f"{name:24} {desc}")
    return rows


def ask(query):
    query = str(query).strip().lower()
    if not query:
        return list_templates()
    words = set(re.findall(r"[a-z0-9_]+", query))
    scored = []
    for name in template_names(include_aliases=True):
        canonical = ALIASES.get(name, name)
        code = _read(canonical)
        desc = _description(code).lower()
        haystack = (name.replace("_", " ") + " " + desc + " " + code[:4000]).lower()
        overlap = len(words & set(re.findall(r"[a-z0-9_]+", haystack))) / max(len(words), 1)
        ratio = difflib.SequenceMatcher(None, query, name.replace("_", " ").lower()).ratio()
        score = 0.65 * overlap + 0.35 * ratio
        if score > 0.08:
            scored.append((score, name))
    if not scored:
        print("No matching templates. Try myml.list_templates().")
        return None
    scored.sort(reverse=True)
    return get_template(scored[0][1]).show()
