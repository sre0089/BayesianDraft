from scripts.privacy_scan import scan_repo


def test_privacy_scan_finds_no_repo_matches() -> None:
    assert scan_repo() == []


def test_privacy_scan_skips_ignored_local_data(tmp_path) -> None:
    data_dir = tmp_path / "data" / "processed"
    data_dir.mkdir(parents=True)
    denied_name = "Jus" + "tin"
    (data_dir / "local.json").write_text(f'{{"name": "{denied_name}"}}', encoding="utf-8")

    assert scan_repo(tmp_path) == []
