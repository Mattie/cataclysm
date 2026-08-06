import subprocess
import sys

from snapclass import Stash

from cataclysm import doomed


def test_generate_fresh_code_passes_formatted_info_and_utensils(monkeypatch):
    calls = []

    def fake_generate(formatted_info, utensils=None):
        calls.append((formatted_info, utensils))
        return "_exec_return_values = 5\n"

    monkeypatch.setattr(doomed, "generate_code_with_chatsnack", fake_generate)
    creator = doomed.CataclysmCreator(_utensils=["internal-tool"])

    assert creator._generate_fresh_code("context") == "_exec_return_values = 5\n"
    assert calls == [("context", ["internal-tool"])]


def test_retry_regenerates_and_saves_even_when_cached_code_exists():
    creator = doomed.CataclysmCreator(autoexecute=False, autogenerate=True)
    saved = []

    creator._lookup_old_code = lambda funcname, signature: "cached code"
    creator._generate_fresh_code = lambda formatted_info: "fresh code"
    creator._save_conjured_code = lambda funcname, signature, code: saved.append(
        (funcname, signature, code)
    )

    code = creator._conjure_code("make_thing", "make_thing-0-0", "context", retry=True)

    assert code == "fresh code"
    assert saved == [("make_thing", "make_thing-0-0", "fresh code")]


def test_invalid_generated_code_retries_before_saving():
    creator = doomed.CataclysmCreator(autoexecute=False, autogenerate=True)
    calls = []
    saved = []

    creator._lookup_old_code = lambda funcname, signature: None

    def fake_generate(formatted_info):
        calls.append(formatted_info)
        if len(calls) == 1:
            raise ValueError("Cataclysm response produced placeholder code.")
        return "_exec_return_values = 12\n"

    creator._generate_fresh_code = fake_generate
    creator._save_conjured_code = lambda funcname, signature, code: saved.append(
        (funcname, signature, code)
    )

    code = creator._conjure_code("add_numbers", "add_numbers-2-0-int-int", "context")

    assert code == "_exec_return_values = 12\n"
    assert len(calls) == 2
    assert "Validation error" in calls[1]
    assert saved == [("add_numbers", "add_numbers-2-0-int-int", "_exec_return_values = 12\n")]


def test_importing_cataclysm_does_not_import_plunkylib():
    result = subprocess.run(
        [
            sys.executable,
            "-c",
            "import sys; import cataclysm; print('plunkylib' in sys.modules)",
        ],
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout.strip() == "False"


def test_generated_code_cache_round_trips_through_snapclass(monkeypatch, tmp_path):
    monkeypatch.setattr(doomed, "FUNCTION_CODE_STASH", Stash(tmp_path))
    creator = doomed.CataclysmCreator(autoexecute=False, autogenerate=False)

    creator._save_conjured_code(
        "cached_answer",
        "cached_answer-0-0",
        "_exec_return_values = 42\n",
    )

    assert creator._lookup_old_code("cached_answer", "cached_answer-0-0") == (
        "_exec_return_values = 42\n"
    )
    cache_text = (tmp_path / "function_cached_answer.yml").read_text(encoding="utf-8")
    assert cache_text == (
        "signatures:\n"
        "  cached_answer-0-0: |\n"
        "    _exec_return_values = 42\n"
    )


def test_snapclass_cache_loads_existing_datafiles_yaml(monkeypatch, tmp_path):
    monkeypatch.setattr(doomed, "FUNCTION_CODE_STASH", Stash(tmp_path))
    (tmp_path / "function_legacy_answer.yml").write_text(
        "signatures:\n"
        "  legacy_answer-0-0: |\n"
        "    _exec_return_values = 7\n",
        encoding="utf-8",
    )

    creator = doomed.CataclysmCreator(autoexecute=False, autogenerate=False)

    assert creator._lookup_old_code("legacy_answer", "legacy_answer-0-0") == (
        "_exec_return_values = 7\n"
    )
