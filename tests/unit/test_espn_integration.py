from bayesiandraft.integrations.espn import (
    EspnCredentialStatus,
    EspnSyncStatus,
    dry_run_sync,
    load_espn_config_from_env,
)


def test_espn_config_reports_missing_credentials(monkeypatch) -> None:
    monkeypatch.delenv("ESPN_LEAGUE_ID", raising=False)
    monkeypatch.delenv("ESPN_SWID", raising=False)
    monkeypatch.delenv("ESPN_S2", raising=False)

    config = load_espn_config_from_env(season=2026)

    assert config.credential_status == EspnCredentialStatus.MISSING


def test_espn_dry_run_skips_without_credentials() -> None:
    config = load_espn_config_from_env(season=2026)

    result = dry_run_sync(config)

    assert result.status == EspnSyncStatus.SKIPPED
    assert result.imported_picks == []


def test_espn_dry_run_is_ready_when_configured(monkeypatch) -> None:
    monkeypatch.setenv("ESPN_LEAGUE_ID", "123")
    monkeypatch.setenv("ESPN_SWID", "{anon}")
    monkeypatch.setenv("ESPN_S2", "secret")

    result = dry_run_sync(load_espn_config_from_env(season=2026))

    assert result.status == EspnSyncStatus.READY
    assert result.credential_status == EspnCredentialStatus.CONFIGURED
