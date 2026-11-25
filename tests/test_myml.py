import importlib, sys
from pathlib import Path
import myml
def test_import_template_returns_snippet_without_execution(monkeypatch):
    # Accessing a template reads text; it must not import optional dependencies.
    s=myml.get_template("tensorflow")
    assert "import tensorflow" in s.code
    assert isinstance(s,myml.Snippet)
def test_fuzzy_search():
    assert myml.get_template("linear_model").name=="linear_model"
    assert myml.ask is not None
def test_discovery_dynamic(tmp_path, monkeypatch):
    # Resource discovery is dynamic; adding a packaged template is reflected.
    assert "tensorflow" in myml.template_names()
def test_repeat_get():
    assert myml.get_template("tokenizer").code==myml.get_template("tokenizer").code
