"""Full-block source retrieval indexed only from myml/data/train.txt."""
from __future__ import annotations

import difflib
import math
import re
from collections import Counter
from dataclasses import dataclass
from importlib import resources

from .core import deliver

_TOKEN_RE = re.compile(r"[A-Za-z_]\w*(?:\.[A-Za-z_]\w*)*")
_NUMBERED_PLOT_RE = re.compile(
    r"^\s*#\s*\d+\.\s*(?:heatmap|box\s+plot|scatter\s+plot|line\s+plot|"
    r"bar\s+plot|count\s+plot|histogram|pie\s+chart|pair\s+plot)\b",
    re.IGNORECASE,
)
_SYNONYM_GROUPS = (
    ("km", "kmeans", "k-means"),
    ("scatter", "scatterplot", "sp"),
    ("hist", "histogram", "histplot"),
    ("box", "boxplot", "outlier", "iqr"),
    ("bar", "barplot", "count", "countplot"),
    ("heat", "heatmap", "hm", "corr", "correlation"),
    ("pair", "pairplot"),
    ("pie", "piechart"),
    ("lr", "linear", "linearregression"),
    ("log", "logistic", "logisticregression"),
    ("dt", "tree", "decisiontree", "decisiontreeclassifier"),
    ("rf", "forest", "randomforest", "randomforestclassifier"),
    ("svm", "svc", "supportvectormachine"),
    ("cm", "confusion", "confusionmatrix"),
    ("tts", "split", "train_test_split"),
    ("cv", "crossvalidation", "cross_val_score"),
    ("null", "na", "fillna", "dropna", "missing", "nan"),
    ("tf", "tensorflow", "keras", "cnn"),
    ("tok", "token", "tokenizer", "nltk", "stem", "stemming", "lem",
     "lemma", "lemmatize", "lemmatization", "ngram", "ngrams"),
    ("lam", "lambda", "map", "filter", "reduce"),
)
_SYNONYMS = {}
for _group in _SYNONYM_GROUPS:
    _members = frozenset(_group)
    for _member in _members:
        _SYNONYMS[_member] = _members


@dataclass(frozen=True)
class CodeBlock:
    title: str
    code: str
    index: int
    header_terms: Counter
    identifier_terms: Counter
    text_terms: Counter

    @property
    def line_count(self):
        return len(self.code.splitlines())


def _resource_text():
    """Read the training source using explicit UTF-8 with replacement fallback."""
    resource = resources.files("myml").joinpath("data", "train.txt")
    return resource.read_text(encoding="utf-8", errors="replace")


def _has_executable_content(lines):
    for line in lines:
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if stripped.startswith(("import ", "from ")):
            continue
        return True
    return False


def _has_data_setup_ahead(lines, index):
    lookahead = "".join(lines[index:index + 45])
    if re.search(r"(?m)^\s*df\s*=\s*pd\.read_csv\s*\(", lookahead):
        return True
    if re.search(r"(?m)^\s*nums\s*=", lookahead):
        return True
    if re.search(r"(?m)^\s*txt\s*=", lookahead) and "word_tokenize" in lookahead:
        return True
    return False


def _parse_code_blocks(source):
    """Split at cell/section headers and logical gaps, retaining source lines."""
    lines = source.splitlines(keepends=True)
    if not lines:
        return []

    starts = {0}
    current_start = 0
    index = 0
    while index < len(lines):
        line = lines[index]
        stripped = line.strip()

        if index > current_start:
            if stripped.startswith("# %%"):
                if _has_executable_content(lines[current_start:index]):
                    starts.add(index)
                    current_start = index
            elif _NUMBERED_PLOT_RE.match(line):
                if _has_executable_content(lines[current_start:index]):
                    starts.add(index)
                    current_start = index
            elif stripped.startswith(("import ", "from ")):
                if _has_executable_content(lines[current_start:index]) and _has_data_setup_ahead(lines, index):
                    starts.add(index)
                    current_start = index
                elif stripped == "import nltk" and _has_executable_content(lines[current_start:index]):
                    starts.add(index)
                    current_start = index
                elif stripped == "import seaborn as sns" and _has_executable_content(lines[current_start:index]):
                    starts.add(index)
                    current_start = index
                elif stripped == "from functools import reduce" and _has_executable_content(lines[current_start:index]):
                    starts.add(index)
                    current_start = index

        if not stripped:
            run_end = index
            while run_end < len(lines) and not lines[run_end].strip():
                run_end += 1
            if run_end - index >= 3 and run_end < len(lines):
                starts.add(run_end)
                current_start = run_end
            index = run_end
            continue
        index += 1

    ordered = sorted(starts)
    blocks = []
    for block_index, start in enumerate(ordered):
        end = ordered[block_index + 1] if block_index + 1 < len(ordered) else len(lines)
        code = "".join(lines[start:end])
        if not code.strip():
            continue
        title = _block_title(code)
        comments = "\n".join(
            line.strip().lstrip("#").strip(" -\t")
            for line in code.splitlines()
            if line.lstrip().startswith("#")
        )
        executable = "\n".join(
            line for line in code.splitlines()
            if not line.lstrip().startswith("#")
        )
        blocks.append(
            CodeBlock(
                title=title,
                code=code,
                index=len(blocks),
                header_terms=_identifier_terms(title + "\n" + comments),
                identifier_terms=_identifier_terms(executable),
                text_terms=_identifier_terms(code),
            )
        )
    return blocks


def _block_title(code):
    for line in code.splitlines():
        candidate = line.strip()
        if candidate.startswith("#"):
            candidate = candidate.lstrip("#").strip(" -\t")
            if candidate and not re.fullmatch(r"[-=]+", candidate):
                return candidate[:100]
    lowered = code.lower()
    if "kmeans" in lowered or "k-means" in lowered:
        return "K-Means clustering"
    if "logisticregression" in lowered:
        return "Logistic regression"
    if "linearregression" in lowered:
        return "Linear regression"
    if "decisiontree" in lowered or "randomforest" in lowered:
        return "Machine-learning model examples"
    if "scatterplot" in lowered or "plt.scatter" in lowered:
        return "Scatter plot"
    if "histplot" in lowered:
        return "Histogram"
    if "heatmap" in lowered:
        return "Heatmap"
    if "pairplot" in lowered:
        return "Pair plot"
    if "word_tokenize" in lowered:
        return "Tokenization and n-grams"
    if "lambda" in lowered:
        return "Lambda, map, filter, and reduce"
    if "iqr" in lowered:
        return "IQR outlier handling"
    return "Python / EDA / ML code"


def _identifier_terms(text):
    terms = Counter()
    for raw in _TOKEN_RE.findall(text):
        terms[raw.lower()] += 1
        for dotted in raw.split("."):
            camel = re.sub(r"([A-Z]+)([A-Z][a-z])", r"\1 \2", dotted)
            camel = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", camel)
            parts = [part.lower() for part in re.split(r"[_\W]+", camel) if part]
            for part in parts:
                terms[part] += 1
            if len(parts) > 1:
                terms["".join(parts)] += 1
                acronym = "".join(part[0] for part in parts if part)
                if len(acronym) >= 2:
                    terms[acronym] += 2
                    if len(acronym) > 2:
                        terms[acronym[:2]] += 1
    return terms


def _expand_terms(terms):
    expanded = set(terms)
    for term in tuple(expanded):
        expanded.update(_SYNONYMS.get(term, ()))
    return expanded


def _normal_phrase(text):
    return " ".join(re.findall(r"[a-z0-9]+", text.lower()))


class FullBlockIndex:
    def __init__(self, source=None):
        self.source = _resource_text() if source is None else source
        self.blocks = _parse_code_blocks(self.source)
        self._document_frequency = Counter()
        self._weighted_terms = []
        self._document_lengths = []
        self._average_length = 0.0
        self._prepare()

    def _prepare(self):
        self._document_frequency.clear()
        self._weighted_terms.clear()
        self._document_lengths.clear()
        for block in self.blocks:
            weighted = Counter()
            for term, count in block.header_terms.items():
                weighted[term] += count * 4.5
            for term, count in block.identifier_terms.items():
                weighted[term] += count * 2.8
            for term, count in block.text_terms.items():
                weighted[term] += count * 0.65
            expanded = Counter()
            for term, count in weighted.items():
                expanded[term] += count
                for equivalent in _SYNONYMS.get(term, ()):
                    expanded[equivalent] += count * 0.55
            self._weighted_terms.append(expanded)
            self._document_lengths.append(sum(expanded.values()))
            self._document_frequency.update(expanded.keys())
        self._average_length = (
            sum(self._document_lengths) / len(self._document_lengths)
            if self._document_lengths else 1.0
        )

    def _score(self, query, block_index):
        block = self.blocks[block_index]
        document = self._weighted_terms[block_index]
        doc_length = self._document_lengths[block_index]
        query_terms = _expand_terms(_identifier_terms(query))
        if not query_terms:
            return 0.0

        score = 0.0
        count_docs = max(1, len(self.blocks))
        k1 = 1.5
        b = 0.75
        for term in query_terms:
            frequency = document.get(term, 0.0)
            if not frequency:
                continue
            df = self._document_frequency.get(term, 0)
            idf = math.log(1.0 + (count_docs - df + 0.5) / (df + 0.5))
            denominator = frequency + k1 * (
                1.0 - b + b * doc_length / max(self._average_length, 1e-9)
            )
            score += idf * (frequency * (k1 + 1.0)) / denominator

        query_phrase = _normal_phrase(query)
        header_phrase = _normal_phrase(
            block.title + "\n" + "\n".join(
                line for line in block.code.splitlines()
                if line.lstrip().startswith("#")
            )
        )
        code_phrase = _normal_phrase(block.code)
        if query_phrase and query_phrase in header_phrase:
            score += 12.0 + len(query_phrase.split()) * 2.0
        elif query_phrase and query_phrase in code_phrase:
            score += 5.0

        if query_phrase:
            available_terms = set(document)
            for word in query_phrase.split():
                if len(word) < 4 or word in available_terms:
                    continue
                if difflib.get_close_matches(word, available_terms, n=2, cutoff=0.72):
                    score += 0.8
        return score

    def search(self, query):
        if not self.blocks:
            return []
        ranked = [
            (self._score(str(query), index), block)
            for index, block in enumerate(self.blocks)
        ]
        ranked = [item for item in ranked if item[0] > 0]
        ranked.sort(key=lambda item: (-item[0], item[1].index))
        return [block for _, block in ranked]


_INDEX = FullBlockIndex()


def reload_index():
    """Reload myml/data/train.txt and rebuild the source-block ranking index."""
    global _INDEX
    _INDEX = FullBlockIndex()
    return len(_INDEX.blocks)


def list_blocks():
    """Print and return a numbered inventory of every parsed training block."""
    for number, block in enumerate(_INDEX.blocks, 1):
        print(f"{number}. {block.title} ({block.line_count} lines)")
    return list(_INDEX.blocks)


def sug(query=None, rank=1):
    """Return and insert a complete matching source block; rank is one-based.

    The public API is deliberately defensive for notebook use: indexing,
    ranking, validation, and cell-delivery failures are reported as a message
    and a safe empty result instead of escaping into the notebook.
    """
    try:
        if query is None or not str(query).strip():
            try:
                return list_blocks()
            except Exception as error:
                print(f"myml.sug: unable to list training blocks ({error})")
                return []

        if not isinstance(rank, int) or isinstance(rank, bool) or rank < 1:
            print("myml.sug: rank must be a positive integer")
            return ""

        matches = _INDEX.search(str(query))
        if not matches:
            print(f"myml.sug: no source block matched {query!r}")
            return ""
        if rank > len(matches):
            print(f"myml.sug: rank {rank} is outside the {len(matches)} matches")
            return ""

        selected = matches[rank - 1]
        print(
            f"myml.sug: selected rank {rank} — {selected.title} "
            f"({selected.line_count} lines)"
        )
        for number, block in enumerate(matches[:4], 1):
            if number != rank:
                print(f"  rank {number}: {block.title}")

        try:
            deliver("sug", selected.code, replace=False)
        except Exception as error:
            # Delivery failures must not discard a successful code retrieval.
            print(f"myml.sug: code found but notebook insertion failed ({error})")
        return selected.code
    except Exception as error:
        print(f"myml.sug: unable to retrieve code ({type(error).__name__}: {error})")
        return ""


def suggest(query="", limit=10):
    """Compatibility search returning matching block titles."""
    try:
        return [block.title for block in _INDEX.search(query)[:max(0, int(limit))]]
    except Exception:
        return []


def install_matcher(shell=None):
    """No external completion matcher is required by the source retrieval API."""
    return False
