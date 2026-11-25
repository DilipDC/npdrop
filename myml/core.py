"""Safe, UTF-8 template loading and notebook cell delivery."""
from __future__ import annotations

import html
import sys
from importlib import resources
from pathlib import Path

ALIASES = {
    "LinearRegression": "linear_regression",
    "LogisticRegression": "logistic_regression",
    "tokenizer": "token",
}


def _template_files():
    """Return packaged resources; template Python is never imported or executed."""
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
    """Read a template as UTF-8 text without importing or executing its source."""
    canonical = resolve_template_name(name)
    return _template_files()[canonical].read_text(
        encoding="utf-8",
        errors="replace",
    )


def _description(code: str) -> str:
    for line in code.splitlines():
        candidate = line.strip()
        if candidate.startswith("#"):
            candidate = candidate.lstrip("#").strip(" -\t")
            if candidate:
                return candidate[:180]
    return "Python source template"


def _colab_copy_card(name: str, code: str) -> bool:
    """Show the Colab-only fallback card when scratch-cell creation fails."""
    try:
        from IPython.display import HTML, display

        safe_name = html.escape(name)
        safe_code = html.escape(code)
        card = f"""<div style="border:1px solid #d0d7de;border-radius:12px;padding:14px;margin:8px 0;font-family:system-ui">
<h3 style="margin:0 0 8px">myml · {safe_name}</h3>
<button style="padding:7px 12px;border:0;border-radius:7px;background:#1463d5;color:#fff;cursor:pointer"
onclick="navigator.clipboard.writeText(this.parentElement.querySelector('pre').innerText).then(()=>this.innerText='Copied!')">Copy code</button>
<pre style="white-space:pre-wrap;overflow:auto;max-height:520px;background:#f6f8fa;padding:12px;border-radius:7px"><code>{safe_code}</code></pre>
</div>"""
        display(HTML(card))
        return True
    except Exception:
        return False


def deliver(name: str, code: str, replace: bool = False) -> bool:
    """Insert code in Colab or the next local Jupyter cell.

    Returns True when a notebook delivery mechanism accepted the code. Outside
    notebooks, or when no local payload manager is available, prints the code.
    Local Jupyter never falls back to an HTML copy card.
    """
    source = str(code)

    # Try Colab explicitly first. If Colab is present but its scratch-cell API
    # is missing or raises, use the one-click HTML card as the Colab fallback.
    try:
        import google.colab  # type: ignore  # noqa: F401
    except Exception:
        google_colab_available = False
    else:
        google_colab_available = True

    if google_colab_available:
        try:
            from google.colab import _frontend  # type: ignore

            _frontend.create_scratch_cell(source)
            return True
        except Exception:
            if _colab_copy_card(name, source):
                return True
            print(source, end="" if source.endswith("\n") else "\n")
            return False

    # Local Jupyter/JupyterLab/Notebook 7. Check both the IPython instance and
    # payload manager before accessing write_payload; do not show HTML here.
    try:
        from IPython import get_ipython

        ip = get_ipython()
        if ip is not None:
            payload_manager = getattr(ip, "payload_manager", None)
            writer = getattr(payload_manager, "write_payload", None)
            if callable(writer):
                writer(
                    {
                        "source": "set_next_input",
                        "text": source,
                        "replace": replace,
                    },
                    single=False,
                )
                return True
    except Exception:
        # Missing/broken IPython state must not make sug() or template imports fail.
        pass

    print(source, end="" if source.endswith("\n") else "\n")
    return False


# Backward-compatible private name used by earlier myml releases.
_deliver = deliver


class Snippet:
    """A source snippet; .code is the untouched UTF-8 template text."""

    def __init__(self, name: str, code: str):
        self.name = resolve_template_name(name)
        self.code = code
        self.description = _description(code)

    def show(self):
        deliver(self.name, self.code)
        return self

    def insert(self, replace: bool = False):
        deliver(self.name, self.code, replace=replace)
        return self

    def save(self, filename):
        path = Path(filename)
        path.write_bytes(self.code.encode("utf-8"))
        return path

    def __repr__(self):
        return f"Snippet({self.name!r}: {self.description})"


def get_template(name: str) -> Snippet:
    canonical = resolve_template_name(name)
    return Snippet(canonical, _read(canonical))


def list_templates():
    rows = [(name, _description(_read(name))) for name in template_names()]
    for name, description in rows:
        print(f"{name:24} {description}")
    return rows


def ask(query):
    """Compatibility helper: retrieve a template by name or simple keyword."""
    import difflib
    import re

    query = str(query or "").strip().lower()
    if not query:
        return list_templates()

    ranked = []
    for name in template_names(include_aliases=True):
        canonical = ALIASES.get(name, name)
        code = _read(canonical)
        words = set(re.findall(r"[a-z0-9]+", (name + " " + code).lower()))
        query_words = set(re.findall(r"[a-z0-9]+", query))
        overlap = len(words & query_words) / max(1, len(query_words))
        fuzzy = difflib.SequenceMatcher(
            None, query, name.replace("_", " ").lower()
        ).ratio()
        ranked.append((overlap * 0.7 + fuzzy * 0.3, name))

    ranked.sort(reverse=True)
    if not ranked or ranked[0][0] < 0.08:
        print("No matching templates. Try myml.list_templates().")
        return None
    return get_template(ranked[0][1]).show()
