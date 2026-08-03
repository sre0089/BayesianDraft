from bayesiandraft.release import build_info_from_env


def test_build_info_uses_package_version_by_default(monkeypatch) -> None:
    monkeypatch.delenv("BAYESIANDRAFT_VERSION", raising=False)

    build_info = build_info_from_env()

    assert build_info.name == "bayesiandraft"
    assert build_info.version == "0.1.0"


def test_build_info_reads_environment(monkeypatch) -> None:
    monkeypatch.setenv("BAYESIANDRAFT_VERSION", "1.2.3")
    monkeypatch.setenv("BAYESIANDRAFT_COMMIT_SHA", "abc123")

    build_info = build_info_from_env()

    assert build_info.version == "1.2.3"
    assert build_info.commit_sha == "abc123"
