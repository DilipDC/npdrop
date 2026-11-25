import sys
import types

import pytest

import myml
from myml import core, suggester


def _install_fake_ipython(monkeypatch, shell):
    fake_ipython = types.ModuleType("IPython")
    fake_ipython.get_ipython = lambda: shell
    monkeypatch.setitem(sys.modules, "IPython", fake_ipython)
    monkeypatch.delitem(sys.modules, "google.colab", raising=False)


def test_sug_is_a_direct_top_level_function():
    assert "sug" in myml.__dict__
    assert myml.sug is suggester.sug
    namespace = {}
    exec("from myml import sug", namespace)
    assert namespace["sug"] is myml.sug


def test_sug_supports_scatterplot_and_positional_rank(monkeypatch):
    calls = []

    class PayloadManager:
        def write_payload(self, payload, single=True):
            calls.append((payload.copy(), single))

    _install_fake_ipython(monkeypatch, types.SimpleNamespace(
        payload_manager=PayloadManager()
    ))
    first = myml.sug("scatterplot")
    second = myml.sug("km", 2)

    assert "sns.scatterplot" in first
    assert "KMeans" in second
    assert len(calls) == 2
    assert calls[0][0]["text"] == first
    assert calls[1][0]["text"] == second
    assert all(item[0]["source"] == "set_next_input" for item in calls)
    assert all(item[0]["replace"] is False for item in calls)
    assert all(item[1] is False for item in calls)


def test_resource_reads_use_utf8_and_replace_errors(monkeypatch):
    calls = []
    from importlib import resources

    real_files = resources.files

    class ResourceProxy:
        def __init__(self, resource):
            self.resource = resource

        def joinpath(self, *parts):
            return ResourceProxy(self.resource.joinpath(*parts))

        def iterdir(self):
            return [ResourceProxy(item) for item in self.resource.iterdir()]

        @property
        def name(self):
            return self.resource.name

        def read_text(self, **kwargs):
            calls.append(kwargs.copy())
            return self.resource.read_text(**kwargs)

    monkeypatch.setattr(
        resources,
        "files",
        lambda package: ResourceProxy(real_files(package)),
    )
    assert myml.get_template("cluster").code
    assert suggester._resource_text()
    assert calls
    assert all(call == {"encoding": "utf-8", "errors": "replace"} for call in calls)


def test_local_jupyter_without_ip_instance_prints_instead_of_raising(
    monkeypatch, capsys
):
    _install_fake_ipython(monkeypatch, None)
    assert core.deliver("test", "print('safe')") is False
    assert "print('safe')" in capsys.readouterr().out


def test_local_jupyter_without_payload_manager_prints_without_html(
    monkeypatch, capsys
):
    _install_fake_ipython(monkeypatch, types.SimpleNamespace())
    assert core.deliver("test", "print('safe')") is False
    output = capsys.readouterr().out
    assert "print('safe')" in output
    assert "<button" not in output


def test_local_jupyter_payload_manager_receives_exact_payload(monkeypatch):
    calls = []

    class PayloadManager:
        def write_payload(self, payload, single=True):
            calls.append((payload.copy(), single))

    _install_fake_ipython(monkeypatch, types.SimpleNamespace(
        payload_manager=PayloadManager()
    ))
    assert core.deliver("test", "x = 1\n") is True
    assert calls == [(
        {"source": "set_next_input", "text": "x = 1\n", "replace": False},
        False,
    )]


def test_colab_uses_scratch_cell_first(monkeypatch):
    calls = []
    google = types.ModuleType("google")
    google.__path__ = []
    colab = types.ModuleType("google.colab")
    colab.__path__ = []
    frontend = types.SimpleNamespace(
        create_scratch_cell=lambda code: calls.append(code)
    )
    colab._frontend = frontend
    google.colab = colab
    monkeypatch.setitem(sys.modules, "google", google)
    monkeypatch.setitem(sys.modules, "google.colab", colab)

    assert core.deliver("test", "print('colab')") is True
    assert calls == ["print('colab')"]


def test_colab_scratch_cell_failure_uses_copy_card_only_on_colab(monkeypatch):
    google = types.ModuleType("google")
    google.__path__ = []
    colab = types.ModuleType("google.colab")
    colab.__path__ = []
    colab._frontend = types.SimpleNamespace(
        create_scratch_cell=lambda code: (_ for _ in ()).throw(RuntimeError("no API"))
    )
    google.colab = colab
    monkeypatch.setitem(sys.modules, "google", google)
    monkeypatch.setitem(sys.modules, "google.colab", colab)

    cards = []
    monkeypatch.setattr(
        core, "_colab_copy_card",
        lambda name, code: cards.append((name, code)) or True,
    )
    assert core.deliver("test", "print('fallback')") is True
    assert cards == [("test", "print('fallback')")]


def test_sug_does_not_raise_on_invalid_rank_or_delivery_failure(monkeypatch):
    assert myml.sug("km", 0) == ""
    monkeypatch.setattr(
        suggester, "deliver",
        lambda *args, **kwargs: (_ for _ in ()).throw(RuntimeError("payload unavailable")),
    )
    result = myml.sug("km")
    assert "KMeans" in result


def test_sug_without_arguments_is_safe_and_lists_blocks(monkeypatch, capsys):
    _install_fake_ipython(monkeypatch, None)
    blocks = myml.sug()
    output = capsys.readouterr().out
    assert isinstance(blocks, list)
    assert blocks
    assert "1." in output
