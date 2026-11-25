"""Fast standard-library suggestion engine indexed from packaged template source."""
from __future__ import annotations

import ast
import difflib
import re
from collections import Counter, defaultdict

from .core import ALIASES, _template_files, _read, template_names

_IDENTIFIER_RE = re.compile(r"(?<!\.)\b[A-Za-z_]\w*\b")
_DOTTED_RE = re.compile(r"\b[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)+\b")
_WORD_RE = re.compile(r"[A-Za-z_]\w*")


def _dotted_name(node):
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        parent = _dotted_name(node.value)
        return f"{parent}.{node.attr}" if parent else node.attr
    return ""


class _SymbolVisitor(ast.NodeVisitor):
    def __init__(self, symbols):
        self.symbols = symbols

    def visit_Import(self, node):
        for item in node.names:
            self.symbols[item.asname or item.name.split(".")[0]] += 5
            self.symbols[item.name] += 4

    def visit_ImportFrom(self, node):
        if node.module:
            self.symbols[node.module] += 4
            self.symbols[node.module.split(".")[0]] += 2
        for item in node.names:
            if item.name != "*":
                self.symbols[item.asname or item.name] += 5

    def visit_FunctionDef(self, node):
        self.symbols[node.name] += 6
        self.generic_visit(node)

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node):
        self.symbols[node.name] += 6
        self.generic_visit(node)

    def visit_Name(self, node):
        self.symbols[node.id] += 1

    def visit_Attribute(self, node):
        dotted = _dotted_name(node)
        if dotted:
            self.symbols[dotted] += 5
            self.symbols[node.attr] += 2
        self.generic_visit(node)

    def visit_arg(self, node):
        self.symbols[node.arg] += 1


def _normalise_line(line):
    return re.sub(r"\s+", " ", line.strip())


def _meaningful_lines(code):
    lines = []
    for raw in code.splitlines():
        line = raw.strip()
        if not line or line.startswith("#"):
            continue
        if re.fullmatch(r"[-=]{3,}.*", line):
            continue
        lines.append(line)
    return lines


class BaseCodeIndex:
    def __init__(self):
        self.names = template_names(include_aliases=True)
        self.symbols = Counter()
        self.lines = Counter()
        self.transitions = defaultdict(Counter)
        self.sources = {}
        self.reload()

    def reload(self):
        self.symbols.clear()
        self.lines.clear()
        self.transitions.clear()
        self.sources.clear()
        self.names = template_names(include_aliases=True)
        for name in template_names():
            code = _read(name)
            self.sources[name] = code
            try:
                tree = ast.parse(code)
                _SymbolVisitor(self.symbols).visit(tree)
            except (SyntaxError, ValueError, TypeError):
                # Some notebook fragments include explanatory separators.
                # Regex indexing still captures identifiers from these snippets.
                pass
            for match in _IDENTIFIER_RE.findall(code):
                self.symbols[match] += 1
            for match in _DOTTED_RE.findall(code):
                self.symbols[match] += 4
            code_lines = _meaningful_lines(code)
            previous = None
            for line in code_lines:
                normalized = _normalise_line(line)
                if not normalized:
                    continue
                self.lines[normalized] += 1
                if previous is not None:
                    self.transitions[previous][normalized] += 1
                previous = normalized
        return self

    def suggest(self, prefix="", previous_line=None, limit=15):
        raw = str(prefix or "")
        import_match = re.search(r"\bfrom\s+myml\s+import\s+([A-Za-z_]\w*)?$", raw)
        if import_match or re.search(r"\bfrom\s+myml\s+import\s*$", raw):
            fragment = import_match.group(1) if import_match and import_match.group(1) else ""
            return self._name_suggestions(fragment, limit)

        magic_match = re.search(r"(?:%myml\s+|\bmyml\.)([A-Za-z_]\w*)?$", raw)
        if magic_match:
            fragment = magic_match.group(1) or ""
            return self._name_suggestions(fragment, limit, helpers=True)

        fragment = raw.rsplit("\n", 1)[-1].strip()
        return self._code_suggestions(fragment, previous_line, limit)

    def _name_suggestions(self, fragment, limit, helpers=False):
        items = list(self.names)
        if helpers:
            items.extend(["ask", "suggest", "reload_index", "list_templates", "get_template"])
        matches = [item for item in items if item.lower().startswith(fragment.lower())]
        return matches[:limit]

    def _code_suggestions(self, fragment, previous_line, limit):
        fragment = fragment.strip()
        scored = {}
        previous = _normalise_line(previous_line) if previous_line else None
        next_lines = self.transitions.get(previous, {}) if previous else {}

        # Full source-line completions: prefix matches rank ahead of fuzzy matches.
        for line, frequency in self.lines.items():
            if fragment and line.lower().startswith(fragment.lower()):
                score = 100 + min(frequency, 5)
                if line in next_lines:
                    score += 20 + next_lines[line]
                scored[line] = max(scored.get(line, 0), score)

        # Prefix matches for symbols, including dotted method/attribute chains.
        for symbol, frequency in self.symbols.items():
            if fragment and symbol.lower().startswith(fragment.lower()):
                scored[symbol] = max(scored.get(symbol, 0), 80 + min(frequency, 10))

        # Context transitions are valuable when the current line is empty or partial.
        if next_lines:
            for line, frequency in next_lines.items():
                if not fragment or line.lower().startswith(fragment.lower()):
                    scored[line] = max(scored.get(line, 0), 70 + min(frequency, 10))

        # Fuzzy token matches are lower priority and never replace Jedi matches.
        if fragment and len(fragment) >= 2:
            candidates = set(self.symbols) | set(self.lines)
            for candidate in candidates:
                if candidate in scored:
                    continue
                ratio = difflib.SequenceMatcher(None, fragment.lower(), candidate.lower()).ratio()
                if ratio >= 0.62:
                    scored[candidate] = 30 + ratio * 20

        ranked = sorted(scored, key=lambda item: (-scored[item], item))
        return ranked[:limit]


_INDEX = BaseCodeIndex()


def suggest(prefix="", previous_line=None, limit=15):
    """Return ranked suggestions from all current template files."""
    return _INDEX.suggest(prefix, previous_line=previous_line, limit=limit)


def reload_index():
    """Re-read template resources and rebuild the in-memory suggestion index."""
    _INDEX.reload()
    return _INDEX


def _matcher_result(context):
    """IPython v2 context matcher body; never suppresses built-in/Jedi results."""
    try:
        all_lines = context.full_text.split("\n")
        cursor_line = max(0, min(context.cursor_line, len(all_lines) - 1))
        current_line = all_lines[cursor_line][:context.cursor_position]
        previous = next(
            (line.strip() for line in reversed(all_lines[:cursor_line]) if line.strip()),
            None,
        )
        before_current = current_line
        import_match = re.search(r"\bfrom\s+myml\s+import\s+([A-Za-z_]\w*)?$", before_current)
        import_empty = re.search(r"\bfrom\s+myml\s+import\s*$", before_current)
        module_match = re.search(r"\bmyml\.([A-Za-z_]\w*)?$", before_current)
        magic_match = re.search(r"%myml\s+([A-Za-z_]\w*)?$", before_current)

        from IPython.core.completer import SimpleCompletion

        if import_match or import_empty:
            fragment = import_match.group(1) if import_match and import_match.group(1) else ""
            candidates = _INDEX._name_suggestions(fragment, 50)
            matched_fragment = fragment
        elif module_match or magic_match:
            match = module_match or magic_match
            fragment = match.group(1) or ""
            candidates = _INDEX._name_suggestions(fragment, 50, helpers=True)
            matched_fragment = fragment
        else:
            fragment = current_line.strip()
            if not fragment:
                fragment = context.token or ""
            candidates = _INDEX._code_suggestions(fragment, previous, 30)
            matched_fragment = fragment

        return {
            "completions": [SimpleCompletion(text=item) for item in candidates],
            "matched_fragment": matched_fragment,
            "ordered": True,
            "suppress": False,
        }
    except Exception:
        return {"completions": [], "suppress": False}


def install_matcher(shell=None):
    """Install the v2 matcher where available, with an older hook fallback."""
    try:
        if shell is None:
            from IPython import get_ipython
            shell = get_ipython()
        if shell is None:
            return False
        completer = shell.Completer
        completer.greedy = True
        custom = getattr(completer, "custom_matchers", None)
        if isinstance(custom, list):
            try:
                from IPython.core.completer import context_matcher
                matcher = context_matcher(priority=100, identifier="myml.base_code_index")(_matcher_result)
                matcher_id = getattr(matcher, "matcher_identifier", "myml.base_code_index")
                already = any(getattr(item, "matcher_identifier", None) == matcher_id for item in custom)
                if not already:
                    custom.append(matcher)

                # IPython's built-in custom-completer matcher normally suppresses
                # other matchers for import completions. Keep native/Jedi and myml
                # results together specifically for "from myml import ...".
                if not getattr(completer, "_myml_import_completion_compat", False):
                    original_custom_matcher = getattr(completer, "custom_completer_matcher", None)
                    if original_custom_matcher is not None:
                        @context_matcher(
                            priority=getattr(original_custom_matcher, "matcher_priority", 0),
                            identifier=getattr(original_custom_matcher, "matcher_identifier", "IPCompleter.custom_completer_matcher"),
                        )
                        def keep_import_completions(context):
                            result = original_custom_matcher(context)
                            if re.search(r"\bfrom\s+myml\s+import\b", context.text_until_cursor):
                                result["suppress"] = False
                            return result

                        completer.custom_completer_matcher = keep_import_completions
                    completer._myml_import_completion_compat = True
                return True
            except Exception:
                pass

        def complete(text, line, cursor_pos):
            try:
                if "from myml import" in line:
                    return _INDEX._name_suggestions(text, 50)
                if "%myml" in line or "myml." in line:
                    return _INDEX._name_suggestions(text, 50, helpers=True)
            except Exception:
                return []
            return []

        shell.set_hook("complete_command", complete, str_key="%myml")
        return True
    except Exception:
        return False
