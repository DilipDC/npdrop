"""myml: deliver ready-to-use ML source snippets in notebooks."""
from .core import Snippet, ask, list_templates, get_template, template_names
from .magic import enable_magic

__all__ = list(template_names())

def __getattr__(name):
    if name in template_names():
        snippet = get_template(name)
        snippet.show()
        return snippet
    raise AttributeError(f"module 'myml' has no attribute {name!r}")

def __dir__():
    return sorted(set(globals()) | set(template_names()))

try:
    enable_magic()
except Exception:
    pass
