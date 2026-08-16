import json
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


def test_missing_conditional_result_regenerates_for_current_inputs():
    creator = doomed.CataclysmCreator()
    calls = []
    generated_bodies = iter(
        (
            "if args_in:\n    _exec_return_values = 1\n",
            "_exec_return_values = 7\n",
        )
    )
    creator._get_installed_modules_info = lambda: []
    creator._get_tracelines = lambda: []

    def fake_conjure(funcname, signature, formatted_info, retry=False):
        calls.append(retry)
        return next(generated_bodies)

    creator._conjure_code = fake_conjure

    assert creator.conditional_result() == 7
    assert calls == [False, True]


def test_explicit_none_result_does_not_trigger_regeneration():
    creator = doomed.CataclysmCreator()
    calls = []
    creator._get_installed_modules_info = lambda: []
    creator._get_tracelines = lambda: []

    def fake_conjure(funcname, signature, formatted_info, retry=False):
        calls.append(retry)
        return "_exec_return_values = None\n"

    creator._conjure_code = fake_conjure

    assert creator.none_result() is None
    assert calls == [False]


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


def test_cache_dotenv_lookup_is_cached_per_working_directory(monkeypatch, tmp_path):
    first_dir = tmp_path / "first"
    second_dir = tmp_path / "second"
    first_dir.mkdir()
    second_dir.mkdir()
    find_calls = []
    dotenv_calls = []

    def fake_find_dotenv(*, usecwd):
        assert usecwd is True
        find_calls.append(Path.cwd())
        return str(Path.cwd() / ".env")

    def fake_dotenv_values(path):
        dotenv_calls.append(path)
        return {}

    monkeypatch.setattr(doomed, "find_dotenv", fake_find_dotenv)
    monkeypatch.setattr(doomed, "dotenv_values", fake_dotenv_values)
    monkeypatch.setattr(doomed, "_DOTENV_MANAGED_VALUES", {})
    monkeypatch.setattr(doomed, "FUNCTION_CODE_STASH", Stash(tmp_path / "cache"))
    doomed._load_cache_dotenv.cache_clear()

    try:
        monkeypatch.chdir(first_dir)
        doomed._function_snapshots()
        doomed._function_snapshots()
        monkeypatch.chdir(second_dir)
        doomed._function_snapshots()
    finally:
        doomed._load_cache_dotenv.cache_clear()

    assert find_calls == [first_dir, second_dir]
    assert dotenv_calls == [str(first_dir / ".env"), str(second_dir / ".env")]


def test_cache_dotenv_switches_managed_values_and_preserves_explicit_overrides(tmp_path):
    first_dir = tmp_path / "first-project"
    second_dir = tmp_path / "second-project"
    first_dir.mkdir()
    second_dir.mkdir()
    first_cache = tmp_path / "first-cache"
    second_cache = tmp_path / "second-cache"
    explicit_cache = tmp_path / "explicit-cache"
    first_chats = tmp_path / "first-chats"
    second_chats = tmp_path / "second-chats"
    (first_dir / ".env").write_text(
        f"CATACLYSM_BASE_DIR={first_cache.as_posix()}\n"
        f"CHATSNACK_BASE_DIR={first_chats.as_posix()}\n",
        encoding="utf-8",
    )
    (second_dir / ".env").write_text(
        f"CATACLYSM_BASE_DIR={second_cache.as_posix()}\n"
        f"CHATSNACK_BASE_DIR={second_chats.as_posix()}\n",
        encoding="utf-8",
    )
    env = os.environ.copy()
    env.pop("CATACLYSM_BASE_DIR", None)
    env.pop("CHATSNACK_BASE_DIR", None)
    env["CATACLYSM_LOGS_DIR"] = str(tmp_path / "logs")
    env["PYTHONPATH"] = os.pathsep.join(
        filter(None, (str(REPO_ROOT), env.get("PYTHONPATH")))
    )
    script = (
        "import json, os; "
        "from cataclysm import doomed; "
        f"os.chdir({str(first_dir)!r}); "
        "doomed._function_snapshots(); "
        "values = [[os.environ['CATACLYSM_BASE_DIR'], os.environ['CHATSNACK_BASE_DIR']]]; "
        f"os.chdir({str(second_dir)!r}); "
        "doomed._function_snapshots(); "
        "values.append([os.environ['CATACLYSM_BASE_DIR'], os.environ['CHATSNACK_BASE_DIR']]); "
        f"os.environ['CATACLYSM_BASE_DIR'] = {str(explicit_cache)!r}; "
        f"os.chdir({str(first_dir)!r}); "
        "doomed._function_snapshots(); "
        "values.append([os.environ['CATACLYSM_BASE_DIR'], os.environ['CHATSNACK_BASE_DIR']]); "
        "print(json.dumps(values))"
    )

    result = subprocess.run(
        [sys.executable, "-c", script],
        cwd=tmp_path,
        env=env,
        check=True,
        capture_output=True,
        text=True,
    )

    assert json.loads(result.stdout) == [
        [first_cache.as_posix(), first_chats.as_posix()],
        [second_cache.as_posix(), second_chats.as_posix()],
        [str(explicit_cache), first_chats.as_posix()],
    ]


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
                "import os, sys; "
                "from cataclysm import doom; "
                "print(os.getenv('CATACLYSM_BASE_DIR')); "
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

    assert result.stdout.splitlines() == ["None", "42", "False"]
