import os
from pathlib import Path
import subprocess
import sys

import cataclysm
from ruamel.yaml import YAML

from cataclysm.__main__ import initialize_datafiles


REPO_ROOT = Path(__file__).resolve().parents[1]
CHAT_ASSET_PATHS = (
    REPO_ROOT / "datafiles" / "chatsnack" / "CataclysmQuery.yml",
    REPO_ROOT / "cataclysm" / "default_files" / "datafiles" / "chatsnack" / "CataclysmQuery.yml",
    REPO_ROOT / "examples" / "hangman" / "datafiles" / "chatsnack" / "CataclysmQuery.yml",
    REPO_ROOT / "examples" / "image_resizer" / "datafiles" / "chatsnack" / "CataclysmQuery.yml",
)


def test_cli_and_package_share_initializer():
    assert initialize_datafiles is cataclysm.initialize_datafiles


def test_packaged_env_template_uses_chatsnack_configuration():
    env_template = Path(cataclysm.__path__[0]) / "default_files" / "env.template.cataclysm"
    content = env_template.read_text(encoding="utf-8")

    assert "CHATSNACK_BASE_DIR" in content
    assert "OPENAI_API_KEY" in content
    assert "PLUNKYLIB_BASE_DIR" not in content


def test_packaged_defaults_include_chatsnack_prompt_and_no_plunkylib_assets():
    defaults_root = Path(cataclysm.__path__[0]) / "default_files"
    default_files = {
        path.relative_to(defaults_root).as_posix()
        for path in defaults_root.rglob("*")
        if path.is_file()
    }

    assert "datafiles/chatsnack/CataclysmQuery.yml" in default_files
    assert all("plunkylib" not in path.lower() for path in default_files)


def test_all_chatsnack_assets_use_terra_with_medium_reasoning():
    yaml = YAML(typ="safe")

    for asset_path in CHAT_ASSET_PATHS:
        params = yaml.load(asset_path.read_text(encoding="utf-8"))["params"]
        assert params["model"] == "gpt-5.6-terra"
        assert params["runtime"] == "responses"
        assert params["responses"]["max_output_tokens"] == 50000
        assert params["responses"]["reasoning"]["effort"] == "medium"


def test_initialize_datafiles_copies_chatsnack_defaults(tmp_path):
    initialize_datafiles(base_dir=str(tmp_path))

    assert (tmp_path / "datafiles" / "chatsnack" / "CataclysmQuery.yml").exists()
    assert (tmp_path / "env.template.cataclysm").exists()
    assert not (tmp_path / "datafiles" / "plunkylib").exists()


def test_initialize_datafiles_reads_chatsnack_base_dir_at_call_time(monkeypatch, tmp_path):
    custom_chatsnack_dir = tmp_path / "custom" / "chatsnack"
    monkeypatch.setenv("CHATSNACK_BASE_DIR", str(custom_chatsnack_dir))

    initialize_datafiles(base_dir=str(tmp_path))

    assert (custom_chatsnack_dir / "CataclysmQuery.yml").exists()
    assert not (tmp_path / "datafiles" / "chatsnack" / "CataclysmQuery.yml").exists()
    assert (tmp_path / "env.template.cataclysm").exists()


def test_package_initialize_datafiles_reads_chatsnack_base_dir_at_call_time(
    monkeypatch,
    tmp_path,
):
    custom_chatsnack_dir = tmp_path / "package" / "chatsnack"
    monkeypatch.setenv("CHATSNACK_BASE_DIR", str(custom_chatsnack_dir))

    cataclysm.initialize_datafiles(base_dir=str(tmp_path))

    assert (custom_chatsnack_dir / "CataclysmQuery.yml").exists()
    assert not (tmp_path / "datafiles" / "chatsnack" / "CataclysmQuery.yml").exists()
    assert (tmp_path / "env.template.cataclysm").exists()


def _cli_test_env():
    env = os.environ.copy()
    env.pop("CHATSNACK_BASE_DIR", None)
    env.pop("CATACLYSM_BASE_DIR", None)
    env.pop("CATACLYSM_LOGS_DIR", None)
    env["PYTHONPATH"] = os.pathsep.join(
        filter(None, (str(REPO_ROOT), env.get("PYTHONPATH")))
    )
    return env


def _assert_cli_init(command, tmp_path):
    result = subprocess.run(
        command,
        cwd=tmp_path,
        env=_cli_test_env(),
        text=True,
        capture_output=True,
        check=False,
    )

    assert result.returncode == 0, result.stderr
    assert "cataclysm - initializing datafiles" in result.stdout
    assert (tmp_path / "datafiles" / "chatsnack" / "CataclysmQuery.yml").is_file()
    assert (tmp_path / "env.template.cataclysm").is_file()


def test_module_cli_init_runs_without_undeclared_logging_modules(tmp_path):
    _assert_cli_init([sys.executable, "-m", "cataclysm", "init"], tmp_path)


def test_installed_console_script_init_runs(tmp_path):
    scripts_dir = Path(sys.executable).parent
    script_path = next(
        (
            path
            for name in ("cataclysm", "cataclysm.exe")
            if (path := scripts_dir / name).is_file()
        ),
        None,
    )
    assert script_path is not None, f"No cataclysm console script in {scripts_dir}"

    command = [str(script_path), "init"]
    if script_path.suffix != ".exe":
        command.insert(0, sys.executable)
    _assert_cli_init(command, tmp_path)
