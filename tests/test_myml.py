import hashlib
import sys
import types

import pytest
import myml
from myml import suggester


EXPECTED_GIT_BLOB_SHAS = {
    "cluster": "ba4a7bc471e2add1de092b5b17da2c645eab5c91",
    "iqr": "14a94378eba11bda0932dc8f69b3d3a28c425cca",
    "linear_regression": "6a6dd658fdd75db9e988a6e969b7e50d6279f912",
    "logistic_regression": "dca3e04daa2310b6bcc112a0789c1aa4c8d743b8",
    "model": "21a87876d855a3ebcd8a350c5a106e86dc2d6402",
    "tensorflow": "dedcdb4091ac4e2a0a2888393ac04167baf45a71",
    "token": "0854873b505c38f26ad95feabbfbe70b2620ec57",
}
TRAIN_GIT_BLOB_SHA = "ca7999ede145414c8cd6104e73d1b549fdff098d"


def _git_blob_sha(data):
    header = b"blob " + str(len(data)).encode("ascii") + b"\0"
    return hashlib.sha1(header + data).hexdigest()


def _fake_notebook(monkeypatch):
    calls = []

    class PayloadManager:
        def write_payload(self, payload, single=True):
            calls.append((payload.copy(), single))

    shell = types.SimpleNamespace(payload_manager=PayloadManager())
    ipython = types.ModuleType("IPython")
    ipython.get_ipython = lambda: shell
    monkeypatch.setitem(sys.modules, "IPython", ipython)
    monkeypatch.delitem(sys.modules, "google.colab", raising=False)
    return calls


def test_all_seven_templates_are_exact_repository_raw_blobs():
    filenames = {
        "cluster": "cluster.py",
        "iqr": "iqr.py",
        "linear_regression": "linear_regression.py",
        "logistic_regression": "logistic_regression.py",
        "model": "model.py",
        "tensorflow": "tensorflow.py",
        "token": "token.py",
    }
    assert set(myml.template_names()) == set(filenames)
    resources = __import__("importlib.resources", fromlist=["files"])
    for name, filename in filenames.items():
        raw = resources.files("myml").joinpath("templates", filename).read_bytes()
        assert _git_blob_sha(raw) == EXPECTED_GIT_BLOB_SHAS[name]
        assert myml.get_template(name).code.encode("utf-8") == raw


def test_aliases_resolve_to_the_same_verbatim_source():
    assert myml.get_template("LinearRegression").code == myml.get_template("linear_regression").code
    assert myml.get_template("LogisticRegression").code == myml.get_template("logistic_regression").code
    assert myml.get_template("tokenizer").code == myml.get_template("token").code


def test_repeated_from_import_cluster_queues_a_fresh_payload_each_time(monkeypatch):
    calls = _fake_notebook(monkeypatch)
    namespace = {}
    exec("from myml import cluster", namespace)
    exec("from myml import cluster", namespace)

    expected = myml.get_template("cluster").code
    assert len(calls) == 2
    for payload, single in calls:
        assert payload == {
            "source": "set_next_input",
            "text": expected,
            "replace": False,
        }
        assert single is False
    assert "cluster" not in myml.__dict__


def test_train_is_not_importable_as_a_template_or_package_attribute():
    with pytest.raises((ImportError, AttributeError)):
        exec("from myml import train", {})
    with pytest.raises(AttributeError):
        getattr(myml, "train")


def test_training_file_is_moved_verbatim_and_not_exposed_as_a_template():
    resources = __import__("importlib.resources", fromlist=["files"])
    raw = resources.files("myml").joinpath("data", "train.txt").read_bytes()
    assert _git_blob_sha(raw) == TRAIN_GIT_BLOB_SHA
    assert "train" not in myml.template_names()
    assert "train" not in myml.template_names(include_aliases=True)


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("km", "KMeans(n_clusters=5"),
        ("scatter plot", 'sns.scatterplot(data=df, x="col1"'),
        ("hist", 'sns.histplot(df["col1"]'),
        ("logistic regression", "LogisticRegression()"),
        ("linear regression", "LinearRegression()"),
        ("lambda", "add_ten = lambda"),
    ],
)
def test_sug_returns_full_verbatim_blocks_and_queues_next_cell(
    query, expected, monkeypatch
):
    calls = _fake_notebook(monkeypatch)
    result = myml.sug(query)
    assert expected in result
    assert len(result.splitlines()) >= 3
    assert result in suggester._INDEX.source
    assert len(calls) == 1
    payload, single = calls[0]
    assert payload == {
        "source": "set_next_input",
        "text": result,
        "replace": False,
    }
    assert single is False


def test_sug_rank_selects_the_requested_match_and_prints_ranked_alternatives(
    monkeypatch, capsys
):
    calls = _fake_notebook(monkeypatch)
    result = myml.sug("scatter plot", rank=2)
    output = capsys.readouterr().out
    assert result
    assert "rank 2" in output.lower()
    assert len(calls) == 1
    assert calls[0][0]["text"] == result


def test_sug_without_query_lists_all_parsed_blocks_without_cell_insertion(
    monkeypatch, capsys
):
    calls = _fake_notebook(monkeypatch)
    blocks = myml.sug()
    output = capsys.readouterr().out
    assert blocks
    assert len(blocks) >= 8
    assert "1." in output
    assert calls == []


def test_typo_tolerance_and_shorthand_expansions():
    assert suggester.suggest("sactter plot")
    assert suggester.suggest("hm")
    assert suggester.suggest("tok")
    assert suggester.suggest("rf")


def test_templates_are_read_as_resources_not_executed(monkeypatch):
    import builtins
    original_import = builtins.__import__

    def forbidden_import(name, *args, **kwargs):
        if name.split(".")[0] in {"sklearn", "tensorflow", "pandas", "numpy", "nltk"}:
            raise AssertionError(f"template code was executed: {name}")
        return original_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", forbidden_import)
    for name in myml.template_names():
        assert myml.get_template(name).code
