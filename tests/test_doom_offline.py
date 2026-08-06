import os
from pathlib import Path
import subprocess
import sys

from snapclass import Stash

from cataclysm import doomed


REPO_ROOT = Path(__file__).resolve().parents[1]


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


def test_cache_stash_refreshes_environment_path_at_call_time(monkeypatch, tmp_path):
    default_code_dir = tmp_path / "default-code"
    configured_code_dir = tmp_path / "configured-code"
    configured_code_dir.mkdir()
    (configured_code_dir / "function_refreshed_answer.yml").write_text(
        "signatures:\n"
        "  refreshed_answer-0-0: |\n"
        "    _exec_return_values = 9\n",
        encoding="utf-8",
    )
    stash = Stash(default_code_dir, env="CATACLYSM_BASE_DIR")
    monkeypatch.delenv("CATACLYSM_BASE_DIR", raising=False)
    assert stash.path == default_code_dir.resolve()
    monkeypatch.setattr(doomed, "FUNCTION_CODE_STASH", stash)
    monkeypatch.setenv("CATACLYSM_BASE_DIR", str(configured_code_dir))

    creator = doomed.CataclysmCreator(autoexecute=False, autogenerate=False)

    assert creator._lookup_old_code("refreshed_answer", "refreshed_answer-0-0") == (
        "_exec_return_values = 9\n"
    )


def test_chosen_loads_cache_path_configured_only_in_dotenv(tmp_path):
    cache_root = tmp_path / "configured-cache"
    code_dir = cache_root / "code"
    code_dir.mkdir(parents=True)
    (code_dir / "function_cached_answer.yml").write_text(
        "signatures:\n"
        "  cached_answer-0-0: |\n"
        "    _exec_return_values = 42\n",
        encoding="utf-8",
    )
    (tmp_path / ".env").write_text(
        f"CATACLYSM_BASE_DIR={cache_root.as_posix()}\n",
        encoding="utf-8",
    )
    env = os.environ.copy()
    env.pop("CATACLYSM_BASE_DIR", None)
    env["CATACLYSM_LOGS_DIR"] = str(tmp_path / "logs")
    env["PYTHONPATH"] = os.pathsep.join(
        filter(None, (str(REPO_ROOT), env.get("PYTHONPATH")))
    )

    result = subprocess.run(
        [
            sys.executable,
            "-c",
            (
                "import sys; "
                "from cataclysm import doom; "
                "print(doom.chosen.cached_answer()); "
                "print('chatsnack' in sys.modules)"
            ),
        ],
        cwd=tmp_path,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )

    assert result.stdout.splitlines() == ["42", "False"]
