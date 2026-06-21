import cataclysm
from cataclysm.__main__ import initialize_datafiles


def test_initialize_datafiles_copies_chatsnack_defaults(tmp_path):
    initialize_datafiles(base_dir=str(tmp_path))

    assert (tmp_path / "datafiles" / "chatsnack" / "CataclysmQuery.yml").exists()
    assert (tmp_path / "env.template.cataclysm").exists()


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
