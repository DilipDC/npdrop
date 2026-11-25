"""myml: verbatim ML templates and source-indexed notebook code retrieval."""
import sys

from .core import (
    ALIASES,
    Snippet,
    ask,
    get_template,
    list_templates,
    template_names,
)
from .suggester import reload_index, suggest
from .suggester import sug as sug
from .magic import enable_magic

__all__ = [
    "ALIASES",
    "Snippet",
    "ask",
    "get_template",
    "list_templates",
    "template_names",
    "sug",
    "suggest",
    "reload_index",
] + template_names(include_aliases=True)


def __getattr__(name):
    """Deliver a fresh template cell on every attribute retrieval."""
    if name in template_names(include_aliases=True):
        try:
            caller = sys._getframe(1)
            if caller.f_code.co_name == "_handle_fromlist":
                return get_template(name)
        except Exception:
            pass
        return get_template(name).show()
    raise AttributeError(f"module 'myml' has no attribute {name!r}")


def __dir__():
    return sorted(set(globals()) | set(template_names(include_aliases=True)))


try:
    enable_magic()
except Exception:
    pass
