"""myml: deliver ready-to-use machine-learning source snippets in notebooks."""
from .core import ALIASES, Snippet, ask, get_template, list_templates, template_names
from .suggester import reload_index, suggest
from .magic import enable_magic
import sys

__all__ = [
    "Snippet", "ask", "get_template", "list_templates", "template_names",
    "suggest", "reload_index",
] + template_names(include_aliases=True)


def __getattr__(name):
    # Deliberately do not cache this object in module globals: every import-time
    # attribute access must queue a fresh editable cell.
    if name in template_names(include_aliases=True):
        snippet = get_template(name)
        # CPython checks from-list names once in importlib._handle_fromlist
        # before IMPORT_FROM retrieves the attribute. Do not deliver during that
        # preflight lookup; the actual retrieval immediately follows and delivers.
        try:
            caller = sys._getframe(1)
            if caller.f_code.co_name == "_handle_fromlist":
                return snippet
        except Exception:
            pass
        snippet.show()
        return snippet
    raise AttributeError(f"module 'myml' has no attribute {name!r}")


def __dir__():
    return sorted(set(globals()) | set(template_names(include_aliases=True)))


try:
    enable_magic()
except Exception:
    pass
