from pathlib import Path

import cataclysm
from cataclysm.__main__ import initialize_datafiles


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
