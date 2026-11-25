import ast
import builtins
from types import SimpleNamespace

import myml
from myml import suggester

EXPECTED = {
    "all_model", "cluster", "iqr", "linear_regression",
    "logistic_regression", "tensorflow", "token",
}
ALIASES = {
    "LinearRegression": "linear_regression",
    "LogisticRegression": "logistic_regression",
    "tokenizer": "token",
}


def test_seven_templates_and_aliases_read_without_execution(monkeypatch):
    assert set(myml.template_names()) == EXPECTED
    assert set(ALIASES).issubset(myml.template_names(include_aliases=True))

    original_import = builtins.__import__

    def guarded_import(name, *args, **kwargs):
        if name.split(".")[0] in {"sklearn", "tensorflow", "pandas", "numpy", "matplotlib"}:
            raise AssertionError(f"template code was executed: {name}")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", guarded_import)
    for name in EXPECTED | set(ALIASES):
        snippet = myml.get_template(name)
        assert isinstance(snippet, myml.Snippet)
        assert snippet.name == ALIASES.get(name, name)
        assert snippet.code.startswith("# Description:")


def test_import_attribute_repeatedly_queues_payload(monkeypatch):
    calls = []

    class FakePayloadManager:
        def write_payload(self, payload, single=True):
            calls.append((payload, single))

    fake_shell = SimpleNamespace(payload_manager=FakePayloadManager())
    import IPython
    monkeypatch.setattr(IPython, "get_ipython", lambda: fake_shell)

    for _ in range(2):
        result = myml.__getattr__("all_model")
        assert isinstance(result, myml.Snippet)

    assert len(calls) == 2
    for payload, single in calls:
        assert payload["source"] == "set_next_input"
        assert payload["replace"] is False
        assert "DecisionTreeClassifier" in payload["text"]
        assert not payload["text"].startswith("# Description:")
        assert single is False
    assert "all_model" not in myml.__dict__


def test_suggester_indexes_exact_source_symbols_and_templates():
    suggester.reload_index()
    assert suggester.suggest("from myml import ")[:7] == sorted(EXPECTED)
    assert "LinearRegression" in suggester.suggest("from myml import Linear")
    assert "pd.read_csv" in suggester.suggest("pd.read")
    assert "train_test_split" in suggester.suggest("train_test")
    assert "model.fit" in suggester.suggest("model.f")
    assert "sns.lineplot" in suggester.suggest("sns.line")


def test_contextual_next_line_ranks_following_source_statement():
    suggester.reload_index()
    choices = suggester.suggest("", previous_line="model = LinearRegression()")
    assert choices[0] == "model.fit(X_train, y_train)"


def test_suggester_handles_incomplete_python_and_magic_contexts():
    assert "cluster" in suggester.suggest("%myml cl")
    assert "reload_index" in suggester.suggest("myml.re")
    assert suggester.suggest("from myml import lo")[0] in {"logistic_regression", "LogisticRegression"}


def test_matcher_keeps_native_completions_enabled():
    class Context:
        full_text = "model = LinearRegression()\nmodel.fi"
        cursor_line = 1
        cursor_position = len("model.fi")
        token = "model.fi"

    result = suggester._matcher_result(Context())
    assert result["suppress"] is False
    assert any(getattr(item, "text", None) == "model.fit(X_train, y_train)" for item in result["completions"])


def test_template_python_sources_and_non_importing_resource_access():
    for name in EXPECTED:
        code = myml.get_template(name).code
        # iqr is a preserved notebook fragment containing a separator line.
        if name != "iqr":
            ast.parse("\n".join(code.splitlines()[1:]))


def test_alias_imports_do_not_cache_module_attributes():
    first = myml.__getattr__("LinearRegression")
    second = myml.__getattr__("LinearRegression")
    assert first.name == second.name == "linear_regression"
    assert "LinearRegression" not in myml.__dict__


def test_from_import_statements_create_one_payload_per_template(monkeypatch):
    calls = []

    class FakePayloadManager:
        def write_payload(self, payload, single=True):
            calls.append((payload, single))

    fake_shell = SimpleNamespace(payload_manager=FakePayloadManager())
    import IPython
    monkeypatch.setattr(IPython, "get_ipython", lambda: fake_shell)
    namespace = {}
    exec("from myml import iqr, cluster", namespace)
    exec("from myml import all_model", namespace)
    exec("from myml import all_model", namespace)

    assert len(calls) == 4
    assert [payload["text"].splitlines()[0] for payload, _ in calls] == [
        "q1=df['Annual Income (k$)'].quantile(0.25)",
        "from sklearn.cluster import KMeans",
        "from sklearn.tree import DecisionTreeClassifier",
        "from sklearn.tree import DecisionTreeClassifier",
    ]
    assert all(payload["source"] == "set_next_input" for payload, _ in calls)
    assert all(payload["replace"] is False and single is False for payload, single in calls)


def test_live_ipython_v2_matcher_keeps_from_import_and_jedi_completions():
    import pytest
    pytest.importorskip("IPython")
    from IPython.core.interactiveshell import InteractiveShell
    from myml.suggester import install_matcher

    shell = InteractiveShell.instance()
    assert install_matcher(shell)
    assert install_matcher(shell)
    ids = [getattr(item, "matcher_identifier", None) for item in shell.Completer.custom_matchers]
    assert ids.count("myml.base_code_index") == 1

    line = "from myml import "
    results = shell.Completer._complete(
        cursor_line=0,
        cursor_pos=len(line),
        line_buffer=line,
        text="",
        full_text=line,
    )
    assert "myml.base_code_index" in results
    assert "IPCompleter.jedi_matcher" in results
    assert results["IPCompleter.custom_completer_matcher"]["suppress"] is False
    assert shell.Completer.matches[:7] == sorted(EXPECTED)
