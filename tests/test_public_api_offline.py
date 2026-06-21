import builtins

import pytest

from cataclysm import doomed
from cataclysm.total import consume


def _stabilize_creator(monkeypatch, creator):
    monkeypatch.setattr(creator, "_get_installed_modules_info", lambda: ["testpkg (1.0)"])
    monkeypatch.setattr(creator, "_get_tracelines", lambda: ["test trace"])


def test_consume_intercepts_missing_global_functions(monkeypatch):
    calls = []

    class FakeCataclysmCreator:
        def __getattr__(self, name):
            def generated(*args, **kwargs):
                calls.append((name, args, kwargs))
                return "generated result"

            return generated

    monkeypatch.setattr(doomed, "CataclysmCreator", FakeCataclysmCreator)
    namespace = {"__builtins__": builtins}

    consume(namespace)
    exec("result = missing_function(2, label='x')", namespace, namespace)

    assert namespace["result"] == "generated result"
    assert calls == [("missing_function", (2,), {"label": "x"})]


def test_creator_executes_generated_body_and_returns_exec_value(monkeypatch):
    creator = doomed.CataclysmCreator()
    _stabilize_creator(monkeypatch, creator)
    saved = []

    monkeypatch.setattr(creator, "_lookup_old_code", lambda funcname, signature: None)
    monkeypatch.setattr(
        creator,
        "_save_conjured_code",
        lambda funcname, signature, code: saved.append((funcname, signature, code)),
    )
    monkeypatch.setattr(
        creator,
        "_generate_fresh_code",
        lambda formatted_info: "_exec_return_values = args_in[0] + bonus\n",
    )

    assert creator.add_with_bonus(7, bonus=5) == 12
    assert saved[0][0] == "add_with_bonus"
    assert saved[0][2] == "_exec_return_values = args_in[0] + bonus\n"
    assert saved[0][1].startswith("add_with_bonus-1-1-int-")
    assert saved[0][1].endswith("-bonus")


def test_impending_returns_generated_code_without_executing_it(monkeypatch):
    creator = doomed.CataclysmCreator()
    _stabilize_creator(monkeypatch, creator.impending)
    generated_code = "raise AssertionError('impending should only preview')\n"
    saved = []

    monkeypatch.setattr(creator.impending, "_lookup_old_code", lambda funcname, signature: None)
    monkeypatch.setattr(
        creator.impending,
        "_save_conjured_code",
        lambda funcname, signature, code: saved.append((funcname, signature, code)),
    )
    monkeypatch.setattr(
        creator.impending,
        "_generate_fresh_code",
        lambda formatted_info: generated_code,
    )

    assert creator.impending.preview_possible_code(1) == generated_code
    assert saved == [
        (
            "preview_possible_code",
            "preview_possible_code-1-0-int",
            generated_code,
        )
    ]


def test_chosen_executes_cached_code_without_generation(monkeypatch):
    creator = doomed.CataclysmCreator()
    _stabilize_creator(monkeypatch, creator.chosen)

    monkeypatch.setattr(
        creator.chosen,
        "_lookup_old_code",
        lambda funcname, signature: "_exec_return_values = args_in[0] * 2\n",
    )
    monkeypatch.setattr(
        creator.chosen,
        "_generate_fresh_code",
        lambda formatted_info: pytest.fail("chosen mode should use cached code"),
    )

    assert creator.chosen.double_cached_value(8) == 16


def test_chosen_raises_name_error_when_cached_code_is_missing(monkeypatch):
    creator = doomed.CataclysmCreator()
    _stabilize_creator(monkeypatch, creator.chosen)
    monkeypatch.setattr(creator.chosen, "_lookup_old_code", lambda funcname, signature: None)

    with pytest.raises(NameError, match="No code for function unknown_cached_function"):
        creator.chosen.unknown_cached_function("x")


def test_cached_code_is_reused_without_fresh_generation(monkeypatch):
    creator = doomed.CataclysmCreator(autoexecute=False, autogenerate=True)
    _stabilize_creator(monkeypatch, creator)

    monkeypatch.setattr(
        creator,
        "_lookup_old_code",
        lambda funcname, signature: "_exec_return_values = 'cached'\n",
    )
    monkeypatch.setattr(
        creator,
        "_generate_fresh_code",
        lambda formatted_info: pytest.fail("cached code should be reused"),
    )
    monkeypatch.setattr(
        creator,
        "_save_conjured_code",
        lambda funcname, signature, code: pytest.fail("cached code should not be saved again"),
    )

    assert creator.cached_answer("anything") == "_exec_return_values = 'cached'\n"


def test_runtime_execution_error_triggers_one_retry_with_context(monkeypatch):
    creator = doomed.CataclysmCreator()
    _stabilize_creator(monkeypatch, creator)
    calls = []
    saved = []

    monkeypatch.setattr(creator, "_lookup_old_code", lambda funcname, signature: None)
    monkeypatch.setattr(
        creator,
        "_save_conjured_code",
        lambda funcname, signature, code: saved.append((funcname, signature, code)),
    )

    def fake_generate(formatted_info):
        calls.append(formatted_info)
        if len(calls) == 1:
            return "raise RuntimeError('bad generated code')\n"
        return "_exec_return_values = 'fixed after retry'\n"

    monkeypatch.setattr(creator, "_generate_fresh_code", fake_generate)

    assert creator.flaky_generated_function() == "fixed after retry"
    assert len(calls) == 2
    assert "Errored code:" in calls[1]
    assert "raise RuntimeError('bad generated code')" in calls[1]
    assert "RuntimeError: bad generated code" in calls[1]
    assert saved == [
        (
            "flaky_generated_function",
            "flaky_generated_function-0-0",
            "raise RuntimeError('bad generated code')\n",
        ),
        (
            "flaky_generated_function",
            "flaky_generated_function-0-0",
            "_exec_return_values = 'fixed after retry'\n",
        ),
    ]
