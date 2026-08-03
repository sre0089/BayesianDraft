from scripts.privacy_scan import scan_repo


def test_privacy_scan_finds_no_repo_matches() -> None:
    assert scan_repo() == []
